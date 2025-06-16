import re
from typing import List, Tuple


def quote_hashtags(expr: str) -> str:
    """Surround bare hashtag terms with quotes for proper tokenization."""
    pattern = r'#([^#()]+?)(?=(?:\s+(?:AND|OR|NOT)\b|\s*\)|\s*#|$))'

    def repl(match: re.Match) -> str:
        inner = match.group(1).strip()
        if ' ' in inner and not (inner.startswith('"') and inner.endswith('"')):
            inner = f'"{inner}"'
        return f'tag:{inner}'

    return re.sub(pattern, repl, expr, flags=re.IGNORECASE)


def tokenize_tag_expr(expr: str) -> List[str]:
    """Return a list of tokens for a boolean tag expression."""
    token_re = re.compile(r"\(|\)|\bAND\b|\bOR\b|\bNOT\b|\"[^\"]+\"|[^\s()]+", re.IGNORECASE)
    tokens = token_re.findall(expr)
    return [t.strip('"') for t in tokens]


def parse_tag_expression(tokens: List[str], pos: int = 0) -> Tuple[str, List[str], int]:
    """Recursive descent parser returning SQL and params."""
    def parse_or(p: int) -> Tuple[str, List[str], int]:
        sql, params, p = parse_and(p)
        while p < len(tokens):
            t = tokens[p].upper()
            if t == 'OR':
                p += 1
                rhs_sql, rhs_params, p = parse_and(p)
                sql = f"({sql} OR {rhs_sql})"
                params.extend(rhs_params)
            else:
                break
        return sql, params, p

    def parse_and(p: int) -> Tuple[str, List[str], int]:
        sql, params, p = parse_not(p)
        while p < len(tokens):
            t = tokens[p].upper()
            if t == 'AND':
                p += 1
            elif t in ('OR', ')'):
                break
            else:
                pass
            rhs_sql, rhs_params, p = parse_not(p)
            sql = f"({sql} AND {rhs_sql})"
            params.extend(rhs_params)
        return sql, params, p

    def parse_not(p: int) -> Tuple[str, List[str], int]:
        if p < len(tokens) and tokens[p].upper() == 'NOT':
            p += 1
            sql, params, p = parse_not(p)
            return f"(NOT {sql})", params, p
        return parse_primary(p)

    def parse_primary(p: int) -> Tuple[str, List[str], int]:
        if p >= len(tokens):
            raise ValueError('Unexpected end of expression')
        tok = tokens[p]
        if tok == '(':  # parse subexpression
            sql, params, p = parse_or(p + 1)
            if p >= len(tokens) or tokens[p] != ')':
                raise ValueError('Unmatched parenthesis')
            return sql, params, p + 1
        if tok == ')':
            raise ValueError('Unexpected )')
        return "has_tag(tags, ?)", [tok], p + 1

    return parse_or(pos)


def build_tag_filter_sql(expr: str) -> Tuple[str, List[str]]:
    tokens = tokenize_tag_expr(expr)
    sql, params, pos = parse_tag_expression(tokens)
    if pos != len(tokens):
        raise ValueError('Invalid syntax')
    return sql, params


def tokenize_search_expr(expr: str) -> List[str]:
    token_re = re.compile(r"\(|\)|\bAND\b|\bOR\b|\bNOT\b|[a-zA-Z]+:\"[^\"]+\"|\"[^\"]+\"|[^\s()]+", re.IGNORECASE)
    raw = token_re.findall(expr)
    tokens = []
    for t in raw:
        if ':' in t:
            prefix, rest = t.split(':', 1)
            if rest.startswith('"') and rest.endswith('"'):
                rest = rest[1:-1]
            tokens.append(f"{prefix}:{rest}")
        else:
            if t.startswith('"') and t.endswith('"'):
                t = t[1:-1]
            tokens.append(t)
    return tokens


def parse_search_expression(tokens: List[str], pos: int = 0) -> Tuple[str, List[str], int]:
    def parse_or(p: int) -> Tuple[str, List[str], int]:
        sql, params, p = parse_and(p)
        while p < len(tokens):
            t = tokens[p].upper()
            if t == 'OR':
                p += 1
                rhs_sql, rhs_params, p = parse_and(p)
                sql = f"({sql} OR {rhs_sql})"
                params.extend(rhs_params)
            else:
                break
        return sql, params, p

    def parse_and(p: int) -> Tuple[str, List[str], int]:
        sql, params, p = parse_not(p)
        while p < len(tokens):
            t = tokens[p].upper()
            if t == 'AND':
                p += 1
            elif t in ('OR', ')'):
                break
            else:
                pass
            rhs_sql, rhs_params, p = parse_not(p)
            sql = f"({sql} AND {rhs_sql})"
            params.extend(rhs_params)
        return sql, params, p

    def parse_not(p: int) -> Tuple[str, List[str], int]:
        if p < len(tokens) and tokens[p].upper() == 'NOT':
            p += 1
            sql, params, p = parse_not(p)
            return f"(NOT {sql})", params, p
        return parse_primary(p)

    def term_sql(tok: str) -> Tuple[str, List[str]]:
        lower = tok.lower()
        if lower.startswith('url:'):
            val = tok[4:]
            return "url LIKE ?", [f"%{val}%"]
        if lower.startswith('timestamp:'):
            val = tok[len('timestamp:'):]
            return "CAST(timestamp AS TEXT) LIKE ?", [f"%{val}%"]
        if lower.startswith('http:'):
            val = tok[5:]
            return "CAST(status_code AS TEXT) LIKE ?", [f"%{val}%"]
        if lower.startswith('mime:'):
            val = tok[5:]
            return "mime_type LIKE ?", [f"%{val}%"]
        if lower.startswith('tag:'):
            return "has_tag(tags, ?)", [tok[4:]]
        return (
            "(" "url LIKE ? OR tags LIKE ? OR CAST(timestamp AS TEXT) LIKE ? OR "
            "CAST(status_code AS TEXT) LIKE ? OR mime_type LIKE ?" ")",
            [f"%{tok}%"] * 5,
        )

    def parse_primary(p: int) -> Tuple[str, List[str], int]:
        if p >= len(tokens):
            raise ValueError('Unexpected end of expression')
        tok = tokens[p]
        if tok == '(':  # subexpression
            sql, params, p = parse_or(p + 1)
            if p >= len(tokens) or tokens[p] != ')':
                raise ValueError('Unmatched parenthesis')
            return sql, params, p + 1
        if tok == ')':
            raise ValueError('Unexpected )')
        sql, params = term_sql(tok)
        return sql, params, p + 1

    return parse_or(pos)


def build_search_sql(expr: str) -> Tuple[str, List[str]]:
    expr = quote_hashtags(expr)
    tokens = tokenize_search_expr(expr)
    sql, params, pos = parse_search_expression(tokens)
    if pos != len(tokens):
        raise ValueError('Invalid syntax')
    return sql, params
