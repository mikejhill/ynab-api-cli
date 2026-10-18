"""Generated request and response models."""

from __future__ import annotations

from ynab_api_cli.generated.models.account import Account
from ynab_api_cli.generated.models.account_base import AccountBase
from ynab_api_cli.generated.models.account_response import AccountResponse
from ynab_api_cli.generated.models.account_response_data import AccountResponseData
from ynab_api_cli.generated.models.account_type import AccountType
from ynab_api_cli.generated.models.accounts_response import AccountsResponse
from ynab_api_cli.generated.models.accounts_response_data import AccountsResponseData
from ynab_api_cli.generated.models.bulk_response import BulkResponse
from ynab_api_cli.generated.models.bulk_response_data import BulkResponseData
from ynab_api_cli.generated.models.bulk_response_data_bulk import BulkResponseDataBulk
from ynab_api_cli.generated.models.bulk_transactions import BulkTransactions
from ynab_api_cli.generated.models.categories_response import CategoriesResponse
from ynab_api_cli.generated.models.categories_response_data import (
    CategoriesResponseData,
)
from ynab_api_cli.generated.models.category import Category
from ynab_api_cli.generated.models.category_base import CategoryBase
from ynab_api_cli.generated.models.category_group import CategoryGroup
from ynab_api_cli.generated.models.category_group_with_categories import (
    CategoryGroupWithCategories,
)
from ynab_api_cli.generated.models.category_response import CategoryResponse
from ynab_api_cli.generated.models.category_response_data import CategoryResponseData
from ynab_api_cli.generated.models.currency_format_type_0 import CurrencyFormatType0
from ynab_api_cli.generated.models.date_format_type_0 import DateFormatType0
from ynab_api_cli.generated.models.debt_1 import Debt1
from ynab_api_cli.generated.models.debt_2 import Debt2
from ynab_api_cli.generated.models.debt_3 import Debt3
from ynab_api_cli.generated.models.error_detail import ErrorDetail
from ynab_api_cli.generated.models.error_response import ErrorResponse
from ynab_api_cli.generated.models.existing_category import ExistingCategory
from ynab_api_cli.generated.models.existing_transaction import ExistingTransaction
from ynab_api_cli.generated.models.flag_1 import Flag1
from ynab_api_cli.generated.models.flag_2 import Flag2
from ynab_api_cli.generated.models.flag_3 import Flag3
from ynab_api_cli.generated.models.get_transactions_by_account_type import (
    GetTransactionsByAccountType,
)
from ynab_api_cli.generated.models.get_transactions_by_category_type import (
    GetTransactionsByCategoryType,
)
from ynab_api_cli.generated.models.get_transactions_by_month_type import (
    GetTransactionsByMonthType,
)
from ynab_api_cli.generated.models.get_transactions_by_payee_type import (
    GetTransactionsByPayeeType,
)
from ynab_api_cli.generated.models.get_transactions_type import GetTransactionsType
from ynab_api_cli.generated.models.goal_1 import Goal1
from ynab_api_cli.generated.models.goal_2 import Goal2
from ynab_api_cli.generated.models.goal_3 import Goal3
from ynab_api_cli.generated.models.hybrid_transaction import HybridTransaction
from ynab_api_cli.generated.models.hybrid_transaction_type import HybridTransactionType
from ynab_api_cli.generated.models.hybrid_transactions_response import (
    HybridTransactionsResponse,
)
from ynab_api_cli.generated.models.hybrid_transactions_response_data import (
    HybridTransactionsResponseData,
)
from ynab_api_cli.generated.models.loan_account_periodic_value_type_0 import (
    LoanAccountPeriodicValueType0,
)
from ynab_api_cli.generated.models.money_movement import MoneyMovement
from ynab_api_cli.generated.models.money_movement_base import MoneyMovementBase
from ynab_api_cli.generated.models.money_movement_group import MoneyMovementGroup
from ynab_api_cli.generated.models.money_movement_groups_response import (
    MoneyMovementGroupsResponse,
)
from ynab_api_cli.generated.models.money_movement_groups_response_data import (
    MoneyMovementGroupsResponseData,
)
from ynab_api_cli.generated.models.money_movements_response import (
    MoneyMovementsResponse,
)
from ynab_api_cli.generated.models.money_movements_response_data import (
    MoneyMovementsResponseData,
)
from ynab_api_cli.generated.models.month_detail import MonthDetail
from ynab_api_cli.generated.models.month_detail_base import MonthDetailBase
from ynab_api_cli.generated.models.month_detail_response import MonthDetailResponse
from ynab_api_cli.generated.models.month_detail_response_data import (
    MonthDetailResponseData,
)
from ynab_api_cli.generated.models.month_summaries_response import (
    MonthSummariesResponse,
)
from ynab_api_cli.generated.models.month_summaries_response_data import (
    MonthSummariesResponseData,
)
from ynab_api_cli.generated.models.month_summary import MonthSummary
from ynab_api_cli.generated.models.month_summary_base import MonthSummaryBase
from ynab_api_cli.generated.models.new_category import NewCategory
from ynab_api_cli.generated.models.new_transaction import NewTransaction
from ynab_api_cli.generated.models.patch_category_group_wrapper import (
    PatchCategoryGroupWrapper,
)
from ynab_api_cli.generated.models.patch_category_wrapper import PatchCategoryWrapper
from ynab_api_cli.generated.models.patch_month_category_wrapper import (
    PatchMonthCategoryWrapper,
)
from ynab_api_cli.generated.models.patch_payee_wrapper import PatchPayeeWrapper
from ynab_api_cli.generated.models.patch_transactions_wrapper import (
    PatchTransactionsWrapper,
)
from ynab_api_cli.generated.models.payee import Payee
from ynab_api_cli.generated.models.payee_location import PayeeLocation
from ynab_api_cli.generated.models.payee_location_response import PayeeLocationResponse
from ynab_api_cli.generated.models.payee_location_response_data import (
    PayeeLocationResponseData,
)
from ynab_api_cli.generated.models.payee_locations_response import (
    PayeeLocationsResponse,
)
from ynab_api_cli.generated.models.payee_locations_response_data import (
    PayeeLocationsResponseData,
)
from ynab_api_cli.generated.models.payee_response import PayeeResponse
from ynab_api_cli.generated.models.payee_response_data import PayeeResponseData
from ynab_api_cli.generated.models.payees_response import PayeesResponse
from ynab_api_cli.generated.models.payees_response_data import PayeesResponseData
from ynab_api_cli.generated.models.plan_detail import PlanDetail
from ynab_api_cli.generated.models.plan_detail_response import PlanDetailResponse
from ynab_api_cli.generated.models.plan_detail_response_data import (
    PlanDetailResponseData,
)
from ynab_api_cli.generated.models.plan_settings import PlanSettings
from ynab_api_cli.generated.models.plan_settings_response import PlanSettingsResponse
from ynab_api_cli.generated.models.plan_settings_response_data import (
    PlanSettingsResponseData,
)
from ynab_api_cli.generated.models.plan_summary import PlanSummary
from ynab_api_cli.generated.models.plan_summary_response import PlanSummaryResponse
from ynab_api_cli.generated.models.plan_summary_response_data import (
    PlanSummaryResponseData,
)
from ynab_api_cli.generated.models.post_account_wrapper import PostAccountWrapper
from ynab_api_cli.generated.models.post_category_group_wrapper import (
    PostCategoryGroupWrapper,
)
from ynab_api_cli.generated.models.post_category_wrapper import PostCategoryWrapper
from ynab_api_cli.generated.models.post_payee import PostPayee
from ynab_api_cli.generated.models.post_payee_wrapper import PostPayeeWrapper
from ynab_api_cli.generated.models.post_scheduled_transaction_wrapper import (
    PostScheduledTransactionWrapper,
)
from ynab_api_cli.generated.models.post_transactions_wrapper import (
    PostTransactionsWrapper,
)
from ynab_api_cli.generated.models.put_scheduled_transaction_wrapper import (
    PutScheduledTransactionWrapper,
)
from ynab_api_cli.generated.models.put_transaction_wrapper import PutTransactionWrapper
from ynab_api_cli.generated.models.save_account import SaveAccount
from ynab_api_cli.generated.models.save_account_type import SaveAccountType
from ynab_api_cli.generated.models.save_category import SaveCategory
from ynab_api_cli.generated.models.save_category_goal_frequency import (
    SaveCategoryGoalFrequency,
)
from ynab_api_cli.generated.models.save_category_group import SaveCategoryGroup
from ynab_api_cli.generated.models.save_category_group_response import (
    SaveCategoryGroupResponse,
)
from ynab_api_cli.generated.models.save_category_group_response_data import (
    SaveCategoryGroupResponseData,
)
from ynab_api_cli.generated.models.save_category_response import SaveCategoryResponse
from ynab_api_cli.generated.models.save_category_response_data import (
    SaveCategoryResponseData,
)
from ynab_api_cli.generated.models.save_month_category import SaveMonthCategory
from ynab_api_cli.generated.models.save_payee import SavePayee
from ynab_api_cli.generated.models.save_payee_response import SavePayeeResponse
from ynab_api_cli.generated.models.save_payee_response_data import SavePayeeResponseData
from ynab_api_cli.generated.models.save_scheduled_transaction import (
    SaveScheduledTransaction,
)
from ynab_api_cli.generated.models.save_sub_transaction import SaveSubTransaction
from ynab_api_cli.generated.models.save_transaction_with_id_or_import_id import (
    SaveTransactionWithIdOrImportId,
)
from ynab_api_cli.generated.models.save_transaction_with_optional_fields import (
    SaveTransactionWithOptionalFields,
)
from ynab_api_cli.generated.models.save_transactions_response import (
    SaveTransactionsResponse,
)
from ynab_api_cli.generated.models.save_transactions_response_data import (
    SaveTransactionsResponseData,
)
from ynab_api_cli.generated.models.scheduled_sub_transaction import (
    ScheduledSubTransaction,
)
from ynab_api_cli.generated.models.scheduled_sub_transaction_base import (
    ScheduledSubTransactionBase,
)
from ynab_api_cli.generated.models.scheduled_transaction_detail import (
    ScheduledTransactionDetail,
)
from ynab_api_cli.generated.models.scheduled_transaction_frequency import (
    ScheduledTransactionFrequency,
)
from ynab_api_cli.generated.models.scheduled_transaction_response import (
    ScheduledTransactionResponse,
)
from ynab_api_cli.generated.models.scheduled_transaction_response_data import (
    ScheduledTransactionResponseData,
)
from ynab_api_cli.generated.models.scheduled_transaction_summary import (
    ScheduledTransactionSummary,
)
from ynab_api_cli.generated.models.scheduled_transaction_summary_base import (
    ScheduledTransactionSummaryBase,
)
from ynab_api_cli.generated.models.scheduled_transaction_summary_base_frequency import (
    ScheduledTransactionSummaryBaseFrequency,
)
from ynab_api_cli.generated.models.scheduled_transactions_response import (
    ScheduledTransactionsResponse,
)
from ynab_api_cli.generated.models.scheduled_transactions_response_data import (
    ScheduledTransactionsResponseData,
)
from ynab_api_cli.generated.models.sub_transaction import SubTransaction
from ynab_api_cli.generated.models.sub_transaction_base import SubTransactionBase
from ynab_api_cli.generated.models.transaction_cleared_status import (
    TransactionClearedStatus,
)
from ynab_api_cli.generated.models.transaction_detail import TransactionDetail
from ynab_api_cli.generated.models.transaction_response import TransactionResponse
from ynab_api_cli.generated.models.transaction_response_data import (
    TransactionResponseData,
)
from ynab_api_cli.generated.models.transaction_summary import TransactionSummary
from ynab_api_cli.generated.models.transaction_summary_base import (
    TransactionSummaryBase,
)
from ynab_api_cli.generated.models.transactions_import_response import (
    TransactionsImportResponse,
)
from ynab_api_cli.generated.models.transactions_import_response_data import (
    TransactionsImportResponseData,
)
from ynab_api_cli.generated.models.transactions_response import TransactionsResponse
from ynab_api_cli.generated.models.transactions_response_data import (
    TransactionsResponseData,
)
from ynab_api_cli.generated.models.user import User
from ynab_api_cli.generated.models.user_response import UserResponse
from ynab_api_cli.generated.models.user_response_data import UserResponseData

__all__ = (
    "Account",
    "AccountBase",
    "AccountResponse",
    "AccountResponseData",
    "AccountType",
    "AccountsResponse",
    "AccountsResponseData",
    "BulkResponse",
    "BulkResponseData",
    "BulkResponseDataBulk",
    "BulkTransactions",
    "CategoriesResponse",
    "CategoriesResponseData",
    "Category",
    "CategoryBase",
    "CategoryGroup",
    "CategoryGroupWithCategories",
    "CategoryResponse",
    "CategoryResponseData",
    "CurrencyFormatType0",
    "DateFormatType0",
    "Debt1",
    "Debt2",
    "Debt3",
    "ErrorDetail",
    "ErrorResponse",
    "ExistingCategory",
    "ExistingTransaction",
    "Flag1",
    "Flag2",
    "Flag3",
    "GetTransactionsByAccountType",
    "GetTransactionsByCategoryType",
    "GetTransactionsByMonthType",
    "GetTransactionsByPayeeType",
    "GetTransactionsType",
    "Goal1",
    "Goal2",
    "Goal3",
    "HybridTransaction",
    "HybridTransactionType",
    "HybridTransactionsResponse",
    "HybridTransactionsResponseData",
    "LoanAccountPeriodicValueType0",
    "MoneyMovement",
    "MoneyMovementBase",
    "MoneyMovementGroup",
    "MoneyMovementGroupsResponse",
    "MoneyMovementGroupsResponseData",
    "MoneyMovementsResponse",
    "MoneyMovementsResponseData",
    "MonthDetail",
    "MonthDetailBase",
    "MonthDetailResponse",
    "MonthDetailResponseData",
    "MonthSummariesResponse",
    "MonthSummariesResponseData",
    "MonthSummary",
    "MonthSummaryBase",
    "NewCategory",
    "NewTransaction",
    "PatchCategoryGroupWrapper",
    "PatchCategoryWrapper",
    "PatchMonthCategoryWrapper",
    "PatchPayeeWrapper",
    "PatchTransactionsWrapper",
    "Payee",
    "PayeeLocation",
    "PayeeLocationResponse",
    "PayeeLocationResponseData",
    "PayeeLocationsResponse",
    "PayeeLocationsResponseData",
    "PayeeResponse",
    "PayeeResponseData",
    "PayeesResponse",
    "PayeesResponseData",
    "PlanDetail",
    "PlanDetailResponse",
    "PlanDetailResponseData",
    "PlanSettings",
    "PlanSettingsResponse",
    "PlanSettingsResponseData",
    "PlanSummary",
    "PlanSummaryResponse",
    "PlanSummaryResponseData",
    "PostAccountWrapper",
    "PostCategoryGroupWrapper",
    "PostCategoryWrapper",
    "PostPayee",
    "PostPayeeWrapper",
    "PostScheduledTransactionWrapper",
    "PostTransactionsWrapper",
    "PutScheduledTransactionWrapper",
    "PutTransactionWrapper",
    "SaveAccount",
    "SaveAccountType",
    "SaveCategory",
    "SaveCategoryGoalFrequency",
    "SaveCategoryGroup",
    "SaveCategoryGroupResponse",
    "SaveCategoryGroupResponseData",
    "SaveCategoryResponse",
    "SaveCategoryResponseData",
    "SaveMonthCategory",
    "SavePayee",
    "SavePayeeResponse",
    "SavePayeeResponseData",
    "SaveScheduledTransaction",
    "SaveSubTransaction",
    "SaveTransactionWithIdOrImportId",
    "SaveTransactionWithOptionalFields",
    "SaveTransactionsResponse",
    "SaveTransactionsResponseData",
    "ScheduledSubTransaction",
    "ScheduledSubTransactionBase",
    "ScheduledTransactionDetail",
    "ScheduledTransactionFrequency",
    "ScheduledTransactionResponse",
    "ScheduledTransactionResponseData",
    "ScheduledTransactionSummary",
    "ScheduledTransactionSummaryBase",
    "ScheduledTransactionSummaryBaseFrequency",
    "ScheduledTransactionsResponse",
    "ScheduledTransactionsResponseData",
    "SubTransaction",
    "SubTransactionBase",
    "TransactionClearedStatus",
    "TransactionDetail",
    "TransactionResponse",
    "TransactionResponseData",
    "TransactionSummary",
    "TransactionSummaryBase",
    "TransactionsImportResponse",
    "TransactionsImportResponseData",
    "TransactionsResponse",
    "TransactionsResponseData",
    "User",
    "UserResponse",
    "UserResponseData",
)

from pydantic import BaseModel


class ModelRegistry:
    """Resolve forward references after all models have loaded."""

    @classmethod
    def rebuild(cls) -> None:
        """Resolve generated models against the complete namespace."""
        namespace = globals()
        for value in tuple(namespace.values()):
            if (
                isinstance(value, type)
                and value is not BaseModel
                and issubclass(value, BaseModel)
            ):
                value.model_rebuild(_types_namespace=namespace)


ModelRegistry.rebuild()
