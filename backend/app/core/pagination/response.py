"""Shared pagination response envelope.

Every paginated admin/vizu-pay list endpoint was independently reimplementing
the same page/page_size clamp + total_pages arithmetic + response dict shape
(6 near-identical copies as of this audit). This is the single place that
logic lives now — services build the page's `items` however they need to,
then hand off to `paginated_response()` for the envelope.
"""


def clamp_page_params(page: int, page_size: int, max_page_size: int = 100) -> tuple[int, int]:
    return max(page, 1), min(max(page_size, 1), max_page_size)


def paginated_response(items: list, total: int, page: int, page_size: int) -> dict:
    total_pages = (total + page_size - 1) // page_size if page_size else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(total_pages, 1),
    }
