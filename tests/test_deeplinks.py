import unittest
from modules.deeplinks import parse_payload

class DeepLinkTests(unittest.TestCase):
    def test_current_formats(self):
        for payload,kind,value in [
            ("anime_B2308163","anime","B23-08163"),("saga_naruto","saga","naruto"),
            ("busca_one_piece","search","one piece"),("atalhos_a","shortcut","A"),
            ("atalhos_num","shortcut","NUM"),("atalhos_proibidos","shortcut","PROIBIDOS")]:
            with self.subTest(payload=payload):
                target=parse_payload(payload)
                self.assertEqual((target.kind,target.value),(kind,value))

    def test_legacy_formats(self):
        for payload,kind,value in [
            ("get_17","episode_id","17"),("b2308163","anime","B23-08163"),
            ("B23-8163","anime","B23-8163"),("buscar_one_piece","search","one piece"),
            ("naruto-shippuden","legacy_lookup","naruto-shippuden"),
            ("feedback_reportar","feedback","feedback_reportar")]:
            with self.subTest(payload=payload):
                target=parse_payload(payload)
                self.assertEqual((target.kind,target.value),(kind,value))
                self.assertTrue(target.legacy)

    def test_episode_zero_and_database_season_id(self):
        target=parse_payload("ep_B23-08163_97_0")
        self.assertEqual((target.season_id,target.episode_number),(97,0))

    def test_anime_id_with_underscores(self):
        self.assertEqual(parse_payload("ep_custom_anime_12_1").value,"custom_anime")

    def test_malformed(self):
        for value in ["x"*65,"anime_","saga_","get_-1","get_0","ep_B23-08163_0_1",
                      "ep_B23-08163_1_-1","ep_x_one_1","ep_x_1","busca_", "busca___",
                      "atalhos_12","busca_ação","buscar_one%20piece","abc def"]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):parse_payload(value)

    def test_boundaries(self):
        self.assertEqual(parse_payload("").kind,"home")
        self.assertEqual(parse_payload("a"*64).kind,"legacy_lookup")

if __name__=="__main__":unittest.main()
