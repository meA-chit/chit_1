import unittest

from chit_server import registry


class NeedsChildrenTests(unittest.TestCase):
    def setUp(self):
        self.manifests = registry.load_manifests()
        self.kids = next(m for m in self.manifests.values() if m.get("needs_children"))["id"]

    def test_the_catalog_says_which_module_needs_a_child(self):
        flagged = [m["id"] for m in registry.module_catalog(self.manifests) if m["needs_children"]]
        self.assertEqual(flagged, [self.kids])

    def _document(self, children):
        members = [{"role": "adult"}] + [{"role": "child"}] * children
        return {"modules": ["household", "planner", self.kids], "members": members}

    def test_it_cannot_be_enabled_without_a_child(self):
        with self.assertRaises(ValueError):
            registry.validate_module_selection(self.manifests, self._document(0))
        registry.validate_module_selection(self.manifests, self._document(1))


if __name__ == "__main__":
    unittest.main()
