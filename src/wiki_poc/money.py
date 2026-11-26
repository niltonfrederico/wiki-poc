"""Valores monetários em centavos, sem float.

Todo valor entra e sai como `int` em centavos: float perde precisão em soma de
dinheiro.
"""

from dataclasses import dataclass
from typing import Final

_CENTS_PER_UNIT: Final = 100


class InvalidAmountError(ValueError):
    """Valor ou quantidade fora do domínio aceito."""


def format_brl(cents: int, *, symbol: bool = True) -> str:
    """Formata centavos como real brasileiro.

    Args:
        cents: Valor em centavos. Aceita negativo.
        symbol: Prefixa `R$ ` quando verdadeiro.

    Returns:
        O valor com `.` no milhar e `,` no decimal.

    Examples:
        >>> format_brl(123456)
        'R$ 1.234,56'
        >>> format_brl(-5, symbol=False)
        '-0,05'
    """
    sign = "-" if cents < 0 else ""
    units, rest = divmod(abs(cents), _CENTS_PER_UNIT)
    body = f"{units:,}".replace(",", ".") + f",{rest:02d}"
    prefix = "R$ " if symbol else ""
    return f"{prefix}{sign}{body}"


@dataclass(frozen=True, slots=True)
class Installments:
    """Parcelamento sem juros de um valor em centavos.

    O resto da divisão vai para a primeira parcela: a soma das parcelas fecha
    com o total.

    Attributes:
        total: Valor total em centavos.
        count: Número de parcelas.

    Raises:
        InvalidAmountError: `total` negativo ou `count` menor que 1.

    Note:
        Sem juros por desenho. Juros mudam o total e ficam fora desta classe.
    """

    total: int
    count: int

    def __post_init__(self) -> None:
        if self.total < 0 or self.count < 1:
            raise InvalidAmountError

    def amounts(self) -> list[int]:
        """Valor de cada parcela, em centavos.

        Returns:
            Lista com `count` itens que somam `total`.

        Examples:
            >>> Installments(total=1000, count=3).amounts()
            [334, 333, 333]
        """
        base, rest = divmod(self.total, self.count)
        return [base + rest, *([base] * (self.count - 1))]
