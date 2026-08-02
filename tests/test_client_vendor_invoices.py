from typing import Any

import pytest
from pydantic import BaseModel

from ajera.client import AjeraClient
from ajera.schemas.vendor_invoice import (
    ListVendorInvoicesArguments,
    VendorInvoice,
    VendorInvoicePayment,
)

# =============================================================================
# TEST: Fixtures
# =============================================================================
#
# A miniature stand-in for the tenant the derivation was measured against: the
# paid/unpaid/voided sets partition the book, voided invoices carry
# `Status == "Voided"`, and every other invoice is `Normal`. Keys 10 and 40 are
# unpaid, 20 is paid, 30 is voided.

BOOK: list[dict[str, Any]] = [
    {"VendorInvoiceKey": 10, "Status": "Normal", "Date": "2025-01-01", "VendorKey": 1},
    {"VendorInvoiceKey": 20, "Status": "Normal", "Date": "2025-01-02", "VendorKey": 1},
    {"VendorInvoiceKey": 30, "Status": "Voided", "Date": "2025-01-03", "VendorKey": 2},
    {"VendorInvoiceKey": 40, "Status": "Normal", "Date": "2025-01-04", "VendorKey": 2},
]

PAID_KEYS = {20}


def _install_fake_api(
    monkeypatch: pytest.MonkeyPatch, client: AjeraClient
) -> list[ListVendorInvoicesArguments]:
    """
    Stub out the transport, and return the list of arguments it was called with.

    The stub applies the payment filters the way the live API does, so the
    partition the derivation relies on holds in the fixtures too.
    """
    calls: list[ListVendorInvoicesArguments] = []

    def fake_post(request: BaseModel, exclude: Any = None) -> dict[str, Any]:
        arguments = request.method_arguments
        assert isinstance(arguments, ListVendorInvoicesArguments)
        calls.append(arguments)

        records = BOOK
        if arguments.filter_by_paid:
            records = [r for r in BOOK if r["VendorInvoiceKey"] in PAID_KEYS]
        elif arguments.filter_by_unpaid:
            records = [
                r
                for r in BOOK
                if r["VendorInvoiceKey"] not in PAID_KEYS and r["Status"] != "Voided"
            ]
        elif arguments.filter_by_voided:
            records = [r for r in BOOK if r["Status"] == "Voided"]

        return {
            "ResponseCode": 200,
            "Content": {"VendorInvoices": records, "VendorInvoicesDetails": []},
        }

    monkeypatch.setattr(client, "_post", fake_post)
    monkeypatch.setattr(client, "get_session_token", lambda api_version=1: "token")
    return calls


def _payments(invoices: list[VendorInvoice]) -> dict[int, VendorInvoicePayment | None]:
    return {invoice.vendor_invoice_key: invoice.payment for invoice in invoices}


# =============================================================================
# TEST: payment is opt-in
# =============================================================================


def test_payment_is_none_when_not_requested(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AjeraClient(url="https://example.test/api")
    calls = _install_fake_api(monkeypatch, client)

    invoices = client.list_vendor_invoices()

    assert _payments(invoices) == {10: None, 20: None, 30: None, 40: None}
    assert len(calls) == 1


def test_payment_defaults_to_none_on_the_model() -> None:
    assert VendorInvoice().payment is None


# =============================================================================
# TEST: derivation
# =============================================================================


def test_derives_the_full_partition(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AjeraClient(url="https://example.test/api")
    _install_fake_api(monkeypatch, client)

    invoices = client.list_vendor_invoices(with_payment_status=True)

    assert _payments(invoices) == {
        10: VendorInvoicePayment.unpaid,  # not in the paid key set
        20: VendorInvoicePayment.paid,  # in the paid key set
        30: VendorInvoicePayment.voided,  # from Status == "Voided"
        40: VendorInvoicePayment.unpaid,  # by elimination
    }


def test_derivation_costs_exactly_one_extra_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AjeraClient(url="https://example.test/api")
    calls = _install_fake_api(monkeypatch, client)

    client.list_vendor_invoices(with_payment_status=True)

    # Voided comes off the record's own status, so only the paid set is fetched:
    # the unfiltered call plus one filtered call, never a third for voided.
    assert len(calls) == 2
    assert [call.filter_by_paid for call in calls] == [None, True]
    assert [call.filter_by_voided for call in calls] == [None, None]


def test_voided_is_read_from_status_not_the_paid_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AjeraClient(url="https://example.test/api")
    _install_fake_api(monkeypatch, client)

    invoices = client.list_vendor_invoices(with_payment_status=True)
    voided = [inv for inv in invoices if inv.payment is VendorInvoicePayment.voided]

    assert [inv.vendor_invoice_key for inv in voided] == [30]
    assert all(inv.status == "Voided" for inv in voided)


# =============================================================================
# TEST: the derived call re-issues the caller's filters
# =============================================================================


def test_derived_call_reissues_caller_filters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AjeraClient(url="https://example.test/api")
    calls = _install_fake_api(monkeypatch, client)

    client.list_vendor_invoices(
        with_payment_status=True,
        filter_by_vendor=[1, 2],
        filter_by_earliest_invoice_date="2024-01-01",
        filter_by_greater_than_amount=100.0,
    )

    original, derived = calls
    # The key set has to be drawn from the same population as the records being
    # labelled, so everything but filter_by_paid must match the original call.
    assert derived.model_dump(exclude={"filter_by_paid"}) == original.model_dump(
        exclude={"filter_by_paid"}
    )
    assert derived.filter_by_paid is True
    assert derived.filter_by_vendor == [1, 2]
    assert derived.filter_by_earliest_invoice_date == "2024-01-01"
    assert derived.filter_by_greater_than_amount == 100.0


def test_derived_call_does_not_mutate_the_caller_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AjeraClient(url="https://example.test/api")
    calls = _install_fake_api(monkeypatch, client)

    client.list_vendor_invoices(with_payment_status=True)

    assert calls[0].filter_by_paid is None


# =============================================================================
# TEST: callers who already filtered on payment
# =============================================================================


def test_paid_filter_needs_no_extra_call(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AjeraClient(url="https://example.test/api")
    calls = _install_fake_api(monkeypatch, client)

    invoices = client.list_vendor_invoices(
        with_payment_status=True, filter_by_paid=True
    )

    assert _payments(invoices) == {20: VendorInvoicePayment.paid}
    assert len(calls) == 1


def test_unpaid_filter_needs_no_extra_call(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AjeraClient(url="https://example.test/api")
    calls = _install_fake_api(monkeypatch, client)

    invoices = client.list_vendor_invoices(
        with_payment_status=True, filter_by_unpaid=True
    )

    assert _payments(invoices) == {
        10: VendorInvoicePayment.unpaid,
        40: VendorInvoicePayment.unpaid,
    }
    assert len(calls) == 1


def test_voided_filter_needs_no_extra_call(monkeypatch: pytest.MonkeyPatch) -> None:
    client = AjeraClient(url="https://example.test/api")
    calls = _install_fake_api(monkeypatch, client)

    invoices = client.list_vendor_invoices(
        with_payment_status=True, filter_by_voided=True
    )

    assert _payments(invoices) == {30: VendorInvoicePayment.voided}
    assert len(calls) == 1


# =============================================================================
# TEST: VendorInvoicePayment
# =============================================================================


def test_payment_serializes_to_the_api_vocabulary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = AjeraClient(url="https://example.test/api")
    _install_fake_api(monkeypatch, client)

    invoices = client.list_vendor_invoices(with_payment_status=True)

    assert [inv.model_dump(mode="json")["payment"] for inv in invoices] == [
        "Unpaid",
        "Paid",
        "Voided",
        "Unpaid",
    ]


def test_payment_states_match_the_filter_names() -> None:
    assert [state.value for state in VendorInvoicePayment] == [
        "Paid",
        "Unpaid",
        "Voided",
    ]
