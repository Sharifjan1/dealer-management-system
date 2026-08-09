"""
calculations.py

Handles financial calculations for the Dealer Management System.
It calculates vehicle expenses, total investment, projected profit,
actual profit, and return on investment (ROI).
"""


def calculate_total_expenses(expenses):
    """
    Add together all expenses for a vehicle.
    """

    return sum(
        expense.amount
        for expense in expenses
    )


def calculate_total_investment(
    purchase_price,
    expenses
):
    """
    Calculate how much money has been invested
    into a vehicle in total.
    """

    total_expenses = calculate_total_expenses(
        expenses
    )

    return purchase_price + total_expenses


def calculate_projected_profit(
    purchase_price,
    asking_price,
    expenses
):
    """
    Calculate the expected profit if the vehicle
    sells for the current asking price.
    """

    total_investment = calculate_total_investment(
        purchase_price,
        expenses
    )

    return asking_price - total_investment


def calculate_actual_profit(
    purchase_price,
    sale_price,
    expenses
):
    """
    Calculate the final profit after the vehicle
    has actually been sold.
    """

    if sale_price is None:
        return None

    total_investment = calculate_total_investment(
        purchase_price,
        expenses
    )

    return sale_price - total_investment


def calculate_roi(
    purchase_price,
    sale_price,
    expenses
):
    """
    Calculate return on investment as a percentage.
    """

    if sale_price is None:
        return None

    total_investment = calculate_total_investment(
        purchase_price,
        expenses
    )

    if total_investment == 0:
        return 0

    profit = sale_price - total_investment

    return (
        profit / total_investment
    ) * 100
