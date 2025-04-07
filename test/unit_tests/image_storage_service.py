import pytest
from unittest.mock import patch, MagicMock, mock_open
import io
from PIL import Image
import uuid
from botocore.exceptions import ClientError
from server.services.image_storage import ImageStorage, S3_ENDPOINT_URL

class TestImageStorage:
    @patch('server.services.image_storage.boto3.client')
    def test_init_bucket_exists(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        image_storage = ImageStorage()
        mock_boto_client.assert_called_once()
        mock_s3.head_bucket.assert_called_once_with(Bucket='images')
        mock_s3.create_bucket.assert_not_called()
        assert image_storage.bucket_name == 'images'

    @patch('server.services.image_storage.boto3.client')
    def test_init_bucket_doesnt_exist(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.side_effect = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, 'head_bucket')
        image_storage = ImageStorage()
        mock_boto_client.assert_called_once()
        mock_s3.head_bucket.assert_called_once_with(Bucket='images')
        mock_s3.create_bucket.assert_called_once_with(Bucket='images')

    @patch('server.services.image_storage.uuid.uuid4')
    @patch('server.services.image_storage.Image.open')
    @patch('server.services.image_storage.boto3.client')
    def test_upload_image(self, mock_boto_client, mock_image_open, mock_uuid4):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        mock_uuid = MagicMock()
        mock_uuid.hex = "test_file_name_123"
        mock_uuid4.return_value = mock_uuid
        mock_img = MagicMock()
        mock_img.convert.return_value = mock_img
        mock_img.save.side_effect = lambda f, format: None
        mock_image_open.return_value = mock_img
        mock_file = MagicMock()
        mock_file.file = io.BytesIO(b"test image data")
        image_storage = ImageStorage()
        result = image_storage.upload_image(mock_file)
        mock_image_open.assert_called_with(mock_file.file)
        mock_img.convert.assert_called_with("RGB")
        mock_s3.upload_fileobj.assert_called_once()
        assert result == "test_file_name_123"

    @patch('server.services.image_storage.Image.open')
    @patch('server.services.image_storage.boto3.client')
    def test_upload_image_invalid_format(self, mock_boto_client, mock_image_open):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        mock_image_open.side_effect = Exception("Invalid image")
        mock_file = MagicMock()
        mock_file.file = io.BytesIO(b"invalid image data")
        image_storage = ImageStorage()
        with pytest.raises(ValueError) as excinfo:
            image_storage.upload_image(mock_file)
        assert "Unsupported image format" in str(excinfo.value)

    @patch('server.services.image_storage.boto3.client')
    def test_get_image_url(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        image_storage = ImageStorage()
        url = image_storage.get_image_url("test_image_id")
        assert url == f"{S3_ENDPOINT_URL}/images/test_image_id"

    @patch('server.services.image_storage.boto3.client')
    def test_get_image_success(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        mock_body = MagicMock()
        mock_body.read.return_value = b"test image data"
        mock_s3.get_object.return_value = {'Body': mock_body}
        image_storage = ImageStorage()
        result = image_storage.get_image("test_image_id")
        mock_s3.get_object.assert_called_once_with(Bucket='images', Key='test_image_id')
        assert result == b"test image data"

    @patch('server.services.image_storage.boto3.client')
    def test_get_image_failure(self, mock_boto_client):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        error = ClientError({'Error': {'Code': '404', 'Message': 'Not Found'}}, 'get_object')
        mock_s3.get_object.side_effect = error
        image_storage = ImageStorage()
        result = image_storage.get_image("nonexistent_id")
        mock_s3.get_object.assert_called_once_with(Bucket='images', Key='nonexistent_id')
        assert result is None

    @patch('server.services.image_storage.Image.open')
    @patch('server.services.image_storage.boto3.client')
    def test_upload_default_avatar(self, mock_boto_client, mock_image_open):
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_s3.head_bucket.return_value = {}
        mock_img = MagicMock()
        mock_img.convert.return_value = mock_img
        mock_img.save.side_effect = lambda f, format: None
        mock_image_open.return_value = mock_img
        mock_file = MagicMock()
        mock_file.file = io.BytesIO(b"test avatar data")
        image_storage = ImageStorage()
        result = image_storage.upload_default_avatar(mock_file)
        mock_image_open.assert_called_with(mock_file.file)
        mock_img.convert.assert_called_with("RGB")
        mock_s3.upload_fileobj.assert_called_once()
        assert result == "default_avatar"
