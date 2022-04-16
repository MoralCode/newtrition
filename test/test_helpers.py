import unittest
from helpers import *

class TestHelpers(unittest.TestCase):

    def test_grab_id_from_parens(self):
        self.assertEqual(grab_id_from_parens("javascript:NetNutrition.UI.unitsSelectUnit(1);"), 1)
        self.assertEqual(grab_id_from_parens("javascript:NetNutrition.UI.unitsSelectUnit(65535);"), 65535)


if __name__ == '__main__':
    unittest.main()