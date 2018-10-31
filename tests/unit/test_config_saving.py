# """
# Test Config Saving produces expected results.
# """
#
# import os
# from tempfile import NamedTemporaryFile
#
# import globus_sdk.config
#
# from tests.framework import get_fixture_file_dir, CapturedIOTestCase
#
# SET_CFG = os.path.join(get_fixture_file_dir(), 'sample_configs',
#                        'set_test.cfg')
#
#
# class ConfigSaveTests(CapturedIOTestCase):
#
#     def setUp(self):
#         self.parser = globus_sdk.config.get_parser()
#         self.config = NamedTemporaryFile()
#
#     def tearDown(self):
#         globus_sdk.config._parser = None
#         self.config.close()
#
#     def test_verify_set_config_file(self):
#         self.parser.set_write_config_file(self.config.name)
#         assert self.parser._write_path == self.config.name
#
#     def test_verify_load_from_new_config_file(self):
#         with open(SET_CFG) as ch, NamedTemporaryFile(mode='w+') as new_cfg:
#             new_cfg.file.write(ch.read())
#             new_cfg.file.flush()
#
#             self.parser.set_write_config_file(new_cfg.name)
#             assert self.parser.get('option', 'default') == 'general_value'
#
#     def test_verify_write_config_option(self):
#         self.parser.set_write_config_file(self.config.name)
#         self.parser.set('foo', 'bar', 'mysec')
#         assert self.parser.get('foo', 'mysec') == 'bar'
#
#         self.parser.set('baz', 'car', 'new_sec')
#         assert self.parser.get('baz', 'new_sec') == 'car'
#
#     def test_verify_remove_config_option(self):
#         self.parser.set_write_config_file(self.config.name)
#         self.parser.set('foo', 'bar', 'mysec')
#         assert self.parser.get('foo', 'mysec') == 'bar'
#         self.parser.remove('foo', 'mysec')
#         assert self.parser.get('foo', 'mysec') is None
