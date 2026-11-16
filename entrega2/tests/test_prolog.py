"""Pruebas del chatbot Prolog (requiere SWI-Prolog instalado)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bot_prolog


def p(pregunta: str) -> str:
    return bot_prolog.preguntar(pregunta)


class TestFamilia(unittest.TestCase):
    def test_padre(self):
        self.assertIn("Zeus", p("¿Quién es el padre de Apolo?"))

    def test_madre_con_sinonimo(self):
        self.assertIn("Metis", p("¿Quién es la mamá de Atenea?"))

    def test_hermanos(self):
        r = p("¿Quiénes son los hermanos de Zeus?")
        for n in ["Deméter", "Hades", "Hera", "Hestia", "Poseidón"]:
            self.assertIn(n, r)

    def test_abuelos_regla_derivada(self):
        r = p("¿Quiénes son los abuelos de Apolo?")
        self.assertTrue(all(n in r for n in ["Cronos", "Rea", "Ceo", "Febe"]))

    def test_descendientes_recursivo(self):
        r = p("¿Quiénes son los descendientes de Cronos?")
        self.assertIn("Tritón", r)   # bisnieto: requiere la recursion
        self.assertIn("Heracles", r)

    def test_ancestros(self):
        r = p("¿Quiénes son los ancestros de Apolo?")
        self.assertTrue(all(n in r for n in ["Gaia", "Urano", "Cronos"]))

    def test_hijos_en_comun(self):
        r = p("¿Quiénes son los hijos de Zeus y Hera?")
        self.assertIn("Ares", r)
        self.assertNotIn("Apolo", r)

    def test_contar_hijos(self):
        self.assertIn("11", p("¿Cuántos hijos tiene Zeus?"))

    def test_pareja(self):
        self.assertIn("Afrodita", p("¿Con quién está casado Hefesto?"))


class TestSiNo(unittest.TestCase):
    def test_relacion(self):
        self.assertTrue(p("¿Es Zeus hijo de Cronos?").startswith("Sí"))
        self.assertTrue(p("¿Es Apolo hijo de Poseidón?").startswith("No"))

    def test_concordancia(self):
        self.assertIn("hermano de Artemisa", p("¿Son Apolo y Artemisa hermanos?"))
        self.assertIn("hija de Zeus", p("¿Es Artemisa hija de Zeus?"))

    def test_categoria(self):
        self.assertTrue(p("¿Es Zeus olímpico?").startswith("Sí"))
        self.assertTrue(p("¿Es Heracles un dios?").startswith("No"))

    def test_casados(self):
        self.assertTrue(p("¿Están casados Zeus y Hera?").startswith("Sí"))


class TestAtributos(unittest.TestCase):
    def test_dominio_inverso(self):
        self.assertIn("Poseidón", p("¿Quién es el dios del mar?"))

    def test_dominio(self):
        self.assertIn("música", p("¿De qué es dios Apolo?"))

    def test_simbolos(self):
        self.assertIn("lechuza", p("¿Cuál es el símbolo de Atenea?"))

    def test_alias_romano(self):
        self.assertIn("Zeus", p("¿Quién es Júpiter?"))
        self.assertIn("Júpiter", p("¿Cómo se llama Zeus en Roma?"))

    def test_residencia(self):
        self.assertIn("inframundo", p("¿Dónde vive Hades?"))

    def test_criatura_genero(self):
        self.assertEqual(p("¿Quién mató a Medusa?"), "Medusa fue derrotada por Perseo.")

    def test_descripcion(self):
        self.assertIn("tres cabezas", p("¿Qué es Cerbero?"))

    def test_listado(self):
        self.assertIn("Prometeo", p("¿Quiénes son los titanes?"))


class TestRobustez(unittest.TestCase):
    def test_fuera_de_dominio(self):
        self.assertIn("No pude", p("¿Cuál es la capital de Francia?"))

    def test_dato_no_registrado(self):
        self.assertIn("No tengo registrado", p("¿Quién es el padre de Teseo?"))

    def test_entrada_rara(self):
        self.assertIn("No pude", p("¿¿¿!!!"))
        self.assertIn("No pude", p("asdf qwerty"))


if __name__ == "__main__":
    unittest.main()
