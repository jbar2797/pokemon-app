# examples/sdk_quickstart.py
from __future__ import annotations

from poke_pricer.client import Holding, PokemonClient


def main() -> None:
    with PokemonClient(base_url="http://127.0.0.1:8001", timeout=10.0) as client:
        print("== health ==")
        print(client.health())

        print("\n== catalog ==")
        print(client.catalog_summary())

        print("\n== search 'pik' ==")
        print(client.cards_search("pik"))

        print("\n== detail 2 ==")
        print(client.card_detail(2))

        print("\n== prices 2 ==")
        print(client.card_prices(2, limit=10))

        print("\n== portfolio value (3x that card) ==")
        holdings: list[Holding] = [{"card_id": 2, "quantity": 3.0}]
        print(client.portfolio_value(holdings))


if __name__ == "__main__":
    main()
