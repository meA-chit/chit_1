import unittest

from chit_server import icons


class IconTests(unittest.TestCase):
    def test_a_named_sport_gets_its_own_icon_not_the_generic_one(self):
        self.assertEqual(icons.icon_for("Football training"), "⚽")        # football wins over 'training'
        self.assertEqual(icons.icon_for("Swimming"), "🏊")
        self.assertEqual(icons.icon_for("Piano lesson"), "🎹")
        self.assertEqual(icons.icon_for("Training"), "🏅")                  # only the generic word: generic icon

    def test_german_words_accents_case_and_compounds(self):
        self.assertEqual(icons.icon_for("Fußballtraining"), "⚽")           # a compound
        self.assertEqual(icons.icon_for("FUSSBALL"), "⚽")                  # ß and ss are the same
        self.assertEqual(icons.icon_for("Elternabend für die 6.-11. Klassen"), "👪")
        self.assertEqual(icons.icon_for("Infoabend zu Skilager und ILZ"), "⛷️")   # the specific word wins over 'Infoabend'
        self.assertEqual(icons.icon_for("angekündigter kleiner Leistungsnachweis in Musik (wagn)"), "📝")
        self.assertEqual(icons.icon_for("Rennesaustausch: Franzosen in Erlangen"), "🚌")

    def test_short_words_must_be_whole_words(self):
        self.assertNotEqual(icons.icon_for("Magic show"), "🏅")             # 'ag' is inside 'magic' but is not a word
        self.assertEqual(icons.icon_for("Judo AG"), "🥋")
        self.assertEqual(icons.icon_for("Art club"), "🎨")
        self.assertIsNone(icons.icon_for("Smartphone"))                     # 'art' inside 'smartphone' does not count

    def test_falls_back_to_the_category_then_to_nothing(self):
        self.assertEqual(icons.icon_for("Open evening", "school_care"), "🏫")
        self.assertEqual(icons.icon_for("Something unusual", "sport_activity"), "🏅")
        self.assertIsNone(icons.icon_for("Something unusual"))
        self.assertIsNone(icons.icon_for("Bins", "waste_collection"))
        self.assertIsNone(icons.icon_for(None))

    def test_every_rule_in_the_file_is_well_formed(self):
        rules, categories = icons._rules()
        self.assertGreater(len(rules), 30)
        for icon, words in rules:
            self.assertTrue(icon and words, icon)
        self.assertEqual(len({r[0] for r in rules if r[0] == "🏅"}), 1)


if __name__ == "__main__":
    unittest.main()
