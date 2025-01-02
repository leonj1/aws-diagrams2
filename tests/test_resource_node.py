import unittest
from resource_node import ResourceNode

class TestResourceNode(unittest.TestCase):
    def setUp(self):
        self.test_data = {
            'name': 'TestResource',
            'identifier': 'test-id',
            'is_parent': True,
            'region': 'us-west-2'
        }
        self.node = ResourceNode(**self.test_data)

    def test_initialization(self):
        # Test successful initialization
        node = ResourceNode('TestResource', 'test-id', True)
        self.assertEqual(node.name, 'TestResource')
        self.assertEqual(node.identifier, 'test-id')
        self.assertTrue(node.is_parent)
        self.assertEqual(node.region, 'us-east-1')  # Default region

        # Test initialization with custom region
        node = ResourceNode('TestResource', 'test-id', True, 'us-west-2')
        self.assertEqual(node.region, 'us-west-2')

    def test_validation(self):
        # Test empty name validation
        with self.assertRaises(ValueError) as context:
            ResourceNode('', 'test-id', True)
        self.assertIn('name cannot be empty', str(context.exception))

        # Test empty identifier validation
        with self.assertRaises(ValueError) as context:
            ResourceNode('TestResource', '', True)
        self.assertIn('identifier cannot be empty', str(context.exception))

    def test_str_representation(self):
        # Test __str__ method
        expected_str = "ResourceNode(name='TestResource', identifier='test-id', type=parent)"
        self.assertEqual(str(self.node), expected_str)

        # Test with child node
        child_node = ResourceNode('ChildResource', 'child-id', False)
        expected_child_str = "ResourceNode(name='ChildResource', identifier='child-id', type=child)"
        self.assertEqual(str(child_node), expected_child_str)

    def test_repr_representation(self):
        # Test __repr__ method
        expected_repr = "ResourceNode(name='TestResource', identifier='test-id', is_parent=True)"
        self.assertEqual(repr(self.node), expected_repr)

    def test_display_name(self):
        # Test display_name property
        expected_display = "TestResource (test-id)"
        self.assertEqual(self.node.display_name, expected_display)

    def test_to_dict(self):
        # Test conversion to dictionary
        result = self.node.to_dict()
        self.assertEqual(result, self.test_data)

    def test_from_dict(self):
        # Test creation from dictionary
        node = ResourceNode.from_dict(self.test_data)
        self.assertEqual(node.name, self.test_data['name'])
        self.assertEqual(node.identifier, self.test_data['identifier'])
        self.assertEqual(node.is_parent, self.test_data['is_parent'])
        self.assertEqual(node.region, self.test_data['region'])

        # Test with missing optional field (region)
        data_without_region = self.test_data.copy()
        del data_without_region['region']
        node = ResourceNode.from_dict(data_without_region)
        self.assertEqual(node.region, 'us-east-1')  # Default value

    def test_from_dict_validation(self):
        # Test missing required fields
        invalid_data = {'name': 'TestResource', 'is_parent': True}
        with self.assertRaises(ValueError) as context:
            ResourceNode.from_dict(invalid_data)
        self.assertIn('Missing required fields', str(context.exception))
        self.assertIn('identifier', str(context.exception))

    def test_equality(self):
        # Test node equality
        node1 = ResourceNode('TestResource', 'test-id', True)
        node2 = ResourceNode('TestResource', 'test-id', True)
        self.assertEqual(node1, node2)

        # Test inequality
        node3 = ResourceNode('DifferentResource', 'test-id', True)
        self.assertNotEqual(node1, node3)

if __name__ == '__main__':
    unittest.main()
