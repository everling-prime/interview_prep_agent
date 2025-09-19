from agents.web_researcher import WebResearcher


def test_domain_to_company_name_simple():
    assert WebResearcher._domain_to_company_name("stripe.com") == "Stripe"


def test_domain_to_company_name_multi_level():
    assert WebResearcher._domain_to_company_name("acme.co.uk") == "Acme"


def test_domain_to_company_name_with_subdomain():
    assert WebResearcher._domain_to_company_name("jobs.example.io") == "Example"
