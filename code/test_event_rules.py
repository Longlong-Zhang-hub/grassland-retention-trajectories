# SPDX-License-Identifier: MIT
from run_reproduction import enforce_offline
enforce_offline()
import unittest
from event_rules import *
class SyntheticRules(unittest.TestCase):
 def test_exact_onset(self):self.assertEqual(onset_kind(2000,1,2001,3),{'kind':'EXACT','t0':2001})
 def test_interval_onset(self):self.assertEqual(onset_kind(1985,1,1990,3)['kind'],'INTERVAL')
 def test_other_gap_not_exact(self):self.assertEqual(onset_kind(2000,1,2002,3)['kind'],'UNSUPPORTED_GAP')
 def test_single_year_does_not_exit(self):
  r=first_exit({2000:3,2001:1,2002:3,2003:3},2000);self.assertIsNone(r['e']);self.assertEqual(r['excursions'],[2001])
 def test_two_year_exit_clock(self):
  r=first_exit({2000:3,2001:1,2002:2,2003:3},2000);self.assertEqual((r['e'],r['c']),(2001,2002))
 def test_terminal_unconfirmed_censor(self):
  r=first_exit({2000:3,2001:3,2002:1},2000);self.assertEqual((r['status'],r['censor']),('TERMINAL_UNCONFIRMED',2001))
 def test_missing_not_nontarget(self):self.assertEqual(first_exit({2000:3,2001:None,2002:1},2000)['status'],'MISSING_OBSERVATION')
 def test_return_strictly_after_confirmation(self):
  r=post_exit({2001:1,2002:1,2003:3,2004:3,2005:3,2006:3,2007:3},2002);self.assertEqual(r['q'],2003);self.assertTrue(r['q']>2002)
 def test_H3_H5_separate_support(self):
  r=post_exit({2001:1,2002:1,2003:3,2004:3,2005:3},2002);self.assertTrue(r['H3_eligible']);self.assertFalse(r['H5_eligible']);self.assertIsNone(r['H5_return'])
 def test_H5_complete_no_return_is_zero(self):
  r=post_exit({y:1 for y in range(2001,2008)},2002);self.assertTrue(r['H5_eligible']);self.assertFalse(r['H5_return'])
 def test_qplus4_confirmation(self):
  r=post_exit({2001:1,2002:1,2003:3,2004:3,2005:3,2006:1,2007:1},2002);self.assertTrue(r['reexit_eligible']);self.assertTrue(r['reexit'])
 def test_qplus4_missing_not_zero(self):
  r=post_exit({2001:1,2002:1,2003:3,2004:3,2005:3,2006:1},2002);self.assertFalse(r['reexit_eligible']);self.assertIsNone(r['reexit'])
 def test_qplus4_start_too_late(self):
  r=post_exit({2001:1,2002:1,2003:3,2004:3,2005:3,2006:3,2007:1,2008:1},2002);self.assertFalse(r['reexit'])
 def test_interval_first_not_replaced(self):self.assertIsNone(select_global_first([{'observed_year':1990,'kind':'INTERVAL'},{'observed_year':2003,'kind':'EXACT'}]))
 def test_uint64_exact(self):self.assertEqual(exact_id('18446744073709551615'),'18446744073709551615')
 def test_float_id_rejected(self):
  with self.assertRaises(ValueError):exact_id(9007199254740993.0)
 def test_bad_confirmation_rejected(self):
  with self.assertRaises(ValueError):post_exit({2001:3,2002:1,2003:3},2002)
if __name__=='__main__':unittest.main(verbosity=2)
