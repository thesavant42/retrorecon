from retrorecon import subdomain_utils


def delete_subdomain(root_domain: str, subdomain: str) -> None:
    """Remove ``subdomain`` from ``root_domain``."""
    subdomain_utils.delete_record(root_domain, subdomain)
