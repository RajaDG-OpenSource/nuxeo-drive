from nxdrive.tests.common_unit_test import UnitTestCase
from nxdrive.client import LocalClient
from nxdrive.client import RemoteDocumentClient
from nxdrive.logging_config import get_logger

log = get_logger(__name__)


class TestPermissionHierarchy(UnitTestCase):

    def setUpApp(self):
        super(TestPermissionHierarchy, self).setUpApp(server_profile='permission')

    def tearDownApp(self):
        super(TestPermissionHierarchy, self).tearDownApp(server_profile='permission')

    def test_sync_delete_root(self):
        user_workspace_uid = None
        try:
            # Get remote and local clients
            admin_remote_client = self.root_remote_client
            user_remote_client = RemoteDocumentClient(
                self.nuxeo_url, self.user_1, u'nxdrive-test-device-1',
                self.version, password=self.password_1,
                upload_tmp_dir=self.upload_tmp_dir)
            local_client = LocalClient(self.local_nxdrive_folder_1)

            # Make sure user workspace is created and fetch its uid
            user_workspace_uid = user_remote_client.make_file_in_user_workspace('File in user workspace',
                                                                                filename='USFile.txt')['parentRef']

            # Create test folder in user workspace as test user
            test_folder_uid = user_remote_client.make_folder(user_workspace_uid, 'test_folder')
            # Create a document in the test folder
            user_remote_client.make_file(test_folder_uid, 'test_file.txt', "Some content.")

            # Register test folder as a sync root
            user_remote_client.register_as_root(test_folder_uid)

            # Start engine
            self.engine_1.start()

            # Wait for synchronization
            self.wait_sync(wait_for_async=True)

            # Check locally synchronized content
            self.assertTrue(local_client.exists('/My Docs/test_folder'))
            self.assertTrue(local_client.exists('/My Docs/test_folder/test_file.txt'))

            # Delete test folder
            user_remote_client.delete(test_folder_uid)

            # Wait for synchronization
            self.wait_sync(wait_for_async=True)

            # Check locally synchronized content
            self.assertFalse(local_client.exists('/My Docs/test_folder'))
            self.assertEquals(len(local_client.get_children_info('/My Docs')), 0)
        finally:
            # Cleanup user workspace
            if user_workspace_uid is not None and admin_remote_client.exists(user_workspace_uid):
                admin_remote_client.delete(user_workspace_uid,
                                           use_trash=False)

    def test_sync_delete_shared_folder(self):
        user_workspace_uid = None
        try:
            # Get remote and local clients
            admin_remote_client = self.root_remote_client
            user1_remote_client = RemoteDocumentClient(
                self.nuxeo_url, self.user_1, u'nxdrive-test-device-1',
                self.version, password=self.password_1,
                upload_tmp_dir=self.upload_tmp_dir)
            user2_remote_client = RemoteDocumentClient(
                self.nuxeo_url, self.user_2, u'nxdrive-test-device-2',
                self.version, password=self.password_2,
                upload_tmp_dir=self.upload_tmp_dir)
            local_client_1 = LocalClient(self.local_nxdrive_folder_1)

            # Make sure user1 workspace is created and fetch its uid
            user_workspace_uid = user1_remote_client.make_file_in_user_workspace('File in user workspace',
                                                                                 filename='USFile.txt')['parentRef']

            # Register user workspace as a sync root for user1
            user1_remote_client.register_as_root(user_workspace_uid)

            # Start engine
            self.engine_1.start()

            # Wait for synchronization
            self.wait_sync(wait_for_async=True)
            # Check locally synchronized content
            self.assertTrue(local_client_1.exists('/My Docs'))

            # Create test folder in user workspace as user1
            test_folder_uid = user1_remote_client.make_folder(user_workspace_uid, 'test_folder')
            # Wait for synchronization
            self.wait_sync(wait_for_async=True)
            # Check locally synchronized content
            self.assertTrue(local_client_1.exists('/My Docs/test_folder'))

            # Grant ReadWrite permission to user2 on test folder
            op_input = "doc:" + test_folder_uid
            admin_remote_client.execute("Document.SetACE", op_input=op_input, user="nuxeoDriveTestUser_user_2",
                                        permission="ReadWrite", grant="true")
            # Wait for synchronization
            self.wait_sync(wait_for_async=True)

            # Register test folder as a sync root for user2
            user2_remote_client.register_as_root(test_folder_uid)
            # Wait for synchronization
            self.wait_sync(wait_for_async=True)

            # Delete test folder
            user1_remote_client.delete(test_folder_uid)

            # Synchronize deletion
            self.wait_sync(wait_for_async=True)
            # Check locally synchronized content
            self.assertFalse(local_client_1.exists('/My Docs/test_folder'))
            self.assertEquals(len(local_client_1.get_children_info('/My Docs')), 1)
        finally:
            # Cleanup user workspace
            if user_workspace_uid is not None and admin_remote_client.exists(user_workspace_uid):
                admin_remote_client.delete(user_workspace_uid,
                                           use_trash=False)
