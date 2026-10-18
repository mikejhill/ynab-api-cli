"""Generated declarations; regenerate rather than editing."""

from __future__ import annotations

from enum import StrEnum


class AccountType(StrEnum):
    """Generated contract enumeration."""

    AUTOLOAN = "autoLoan"
    CASH = "cash"
    CHECKING = "checking"
    CREDITCARD = "creditCard"
    LINEOFCREDIT = "lineOfCredit"
    MEDICALDEBT = "medicalDebt"
    MORTGAGE = "mortgage"
    OTHERASSET = "otherAsset"
    OTHERDEBT = "otherDebt"
    OTHERLIABILITY = "otherLiability"
    PERSONALLOAN = "personalLoan"
    SAVINGS = "savings"
    STUDENTLOAN = "studentLoan"
