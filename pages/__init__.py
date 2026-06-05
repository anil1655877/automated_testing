"""Pages package initializer."""
from pages.base_page import BasePage
from pages.login_page import LoginPage
from pages.registration_page import RegistrationPage
from pages.dashboard_page import DashboardPage
from pages.ecommerce_page import EcommercePage
from pages.admin_page import AdminPage

__all__ = [
    "BasePage", "LoginPage", "RegistrationPage",
    "DashboardPage", "EcommercePage", "AdminPage",
]
