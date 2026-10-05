import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bot_prolog


class TestChatbotProlog(unittest.TestCase):
    def test_padre(self):
        self.assertIn("Zeus", bot_prolog.preguntar("¿Quién es el padre de Apolo?"))

    def test_abuelos_regla_derivada(self):
        r = bot_prolog.preguntar("¿Quiénes son los abuelos de Apolo?")
        self.assertTrue(all(n in r for n in ["Cronos", "Rea", "Ceo", "Febe"]))

    def test_si_no(self):
        self.assertTrue(bot_prolog.preguntar("¿Es Zeus hijo de Cronos?").startswith("Sí"))
        self.assertTrue(bot_prolog.preguntar("¿Es Apolo hijo de Poseidón?").startswith("No"))

    def test_dominio_inverso(self):
        self.assertIn("Poseidón", bot_prolog.preguntar("¿Quién es el dios del mar?"))

    def test_alias_romano(self):
        self.assertIn("Zeus", bot_prolog.preguntar("¿Quién es Júpiter?"))

    def test_fuera_de_dominio(self):
        self.assertIn("No pude", bot_prolog.preguntar("¿Cuál es la capital de Francia?"))


if __name__ == "__main__":
    unittest.main()
