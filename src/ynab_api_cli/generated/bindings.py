"""Generated static endpoint dispatch; regenerate to change."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import ClassVar

from ynab_api_cli.generated.api.accounts import create_account as operation1
from ynab_api_cli.generated.api.accounts import get_account_by_id as operation2
from ynab_api_cli.generated.api.accounts import get_accounts as operation3
from ynab_api_cli.generated.api.categories import create_category as operation5
from ynab_api_cli.generated.api.categories import create_category_group as operation6
from ynab_api_cli.generated.api.categories import get_categories as operation7
from ynab_api_cli.generated.api.categories import get_category_by_id as operation8
from ynab_api_cli.generated.api.categories import get_month_category_by_id as operation9
from ynab_api_cli.generated.api.categories import update_category as operation10
from ynab_api_cli.generated.api.categories import update_category_group as operation11
from ynab_api_cli.generated.api.categories import update_month_category as operation12
from ynab_api_cli.generated.api.money_movements import (
    get_money_movement_groups as operation14,
)
from ynab_api_cli.generated.api.money_movements import (
    get_money_movement_groups_by_month as operation15,
)
from ynab_api_cli.generated.api.money_movements import (
    get_money_movements as operation16,
)
from ynab_api_cli.generated.api.money_movements import (
    get_money_movements_by_month as operation17,
)
from ynab_api_cli.generated.api.months import get_plan_month as operation19
from ynab_api_cli.generated.api.months import get_plan_months as operation20
from ynab_api_cli.generated.api.payee_locations import (
    get_payee_location_by_id as operation22,
)
from ynab_api_cli.generated.api.payee_locations import (
    get_payee_locations as operation23,
)
from ynab_api_cli.generated.api.payee_locations import (
    get_payee_locations_by_payee as operation24,
)
from ynab_api_cli.generated.api.payees import create_payee as operation26
from ynab_api_cli.generated.api.payees import get_payee_by_id as operation27
from ynab_api_cli.generated.api.payees import get_payees as operation28
from ynab_api_cli.generated.api.payees import update_payee as operation29
from ynab_api_cli.generated.api.plans import get_plan_by_id as operation31
from ynab_api_cli.generated.api.plans import get_plan_settings_by_id as operation32
from ynab_api_cli.generated.api.plans import get_plans as operation33
from ynab_api_cli.generated.api.scheduled_transactions import (
    create_scheduled_transaction as operation35,
)
from ynab_api_cli.generated.api.scheduled_transactions import (
    delete_scheduled_transaction as operation36,
)
from ynab_api_cli.generated.api.scheduled_transactions import (
    get_scheduled_transaction_by_id as operation37,
)
from ynab_api_cli.generated.api.scheduled_transactions import (
    get_scheduled_transactions as operation38,
)
from ynab_api_cli.generated.api.scheduled_transactions import (
    update_scheduled_transaction as operation39,
)
from ynab_api_cli.generated.api.transactions import create_transaction as operation41
from ynab_api_cli.generated.api.transactions import delete_transaction as operation42
from ynab_api_cli.generated.api.transactions import get_transaction_by_id as operation43
from ynab_api_cli.generated.api.transactions import get_transactions as operation44
from ynab_api_cli.generated.api.transactions import (
    get_transactions_by_account as operation45,
)
from ynab_api_cli.generated.api.transactions import (
    get_transactions_by_category as operation46,
)
from ynab_api_cli.generated.api.transactions import (
    get_transactions_by_month as operation47,
)
from ynab_api_cli.generated.api.transactions import (
    get_transactions_by_payee as operation48,
)
from ynab_api_cli.generated.api.transactions import import_transactions as operation49
from ynab_api_cli.generated.api.transactions import update_transaction as operation50
from ynab_api_cli.generated.api.transactions import update_transactions as operation51
from ynab_api_cli.generated.api.user import get_user as operation53
from ynab_api_cli.transport import Transport
from ynab_api_cli.types import RequestValues, Response


class Bindings:
    """Statically reference every generated typed operation."""

    operations: ClassVar[
        Mapping[str, Callable[[Transport, RequestValues], Response[object]]]
    ] = MappingProxyType(
        {
            "create_account": operation1.Endpoint.dispatch,
            "get_account_by_id": operation2.Endpoint.dispatch,
            "get_accounts": operation3.Endpoint.dispatch,
            "create_category": operation5.Endpoint.dispatch,
            "create_category_group": operation6.Endpoint.dispatch,
            "get_categories": operation7.Endpoint.dispatch,
            "get_category_by_id": operation8.Endpoint.dispatch,
            "get_month_category_by_id": operation9.Endpoint.dispatch,
            "update_category": operation10.Endpoint.dispatch,
            "update_category_group": operation11.Endpoint.dispatch,
            "update_month_category": operation12.Endpoint.dispatch,
            "get_money_movement_groups": operation14.Endpoint.dispatch,
            "get_money_movement_groups_by_month": operation15.Endpoint.dispatch,
            "get_money_movements": operation16.Endpoint.dispatch,
            "get_money_movements_by_month": operation17.Endpoint.dispatch,
            "get_plan_month": operation19.Endpoint.dispatch,
            "get_plan_months": operation20.Endpoint.dispatch,
            "get_payee_location_by_id": operation22.Endpoint.dispatch,
            "get_payee_locations": operation23.Endpoint.dispatch,
            "get_payee_locations_by_payee": operation24.Endpoint.dispatch,
            "create_payee": operation26.Endpoint.dispatch,
            "get_payee_by_id": operation27.Endpoint.dispatch,
            "get_payees": operation28.Endpoint.dispatch,
            "update_payee": operation29.Endpoint.dispatch,
            "get_plan_by_id": operation31.Endpoint.dispatch,
            "get_plan_settings_by_id": operation32.Endpoint.dispatch,
            "get_plans": operation33.Endpoint.dispatch,
            "create_scheduled_transaction": operation35.Endpoint.dispatch,
            "delete_scheduled_transaction": operation36.Endpoint.dispatch,
            "get_scheduled_transaction_by_id": operation37.Endpoint.dispatch,
            "get_scheduled_transactions": operation38.Endpoint.dispatch,
            "update_scheduled_transaction": operation39.Endpoint.dispatch,
            "create_transaction": operation41.Endpoint.dispatch,
            "delete_transaction": operation42.Endpoint.dispatch,
            "get_transaction_by_id": operation43.Endpoint.dispatch,
            "get_transactions": operation44.Endpoint.dispatch,
            "get_transactions_by_account": operation45.Endpoint.dispatch,
            "get_transactions_by_category": operation46.Endpoint.dispatch,
            "get_transactions_by_month": operation47.Endpoint.dispatch,
            "get_transactions_by_payee": operation48.Endpoint.dispatch,
            "import_transactions": operation49.Endpoint.dispatch,
            "update_transaction": operation50.Endpoint.dispatch,
            "update_transactions": operation51.Endpoint.dispatch,
            "get_user": operation53.Endpoint.dispatch,
        }
    )
