import unittest
from unittest.mock import patch, MagicMock
from output_diagram_script import create_diagram, graph_attr, node_attr, edge_attr

class TestOutputDiagramScript(unittest.TestCase):
    @patch('output_diagram_script.Diagram')
    @patch('output_diagram_script.Cluster')
    @patch('output_diagram_script.General')
    @patch('output_diagram_script.RouteTable')
    @patch('output_diagram_script.IAMRole')
    @patch('output_diagram_script.Nacl')
    @patch('output_diagram_script.Fargate')
    def test_create_diagram(self, mock_fargate, mock_nacl, mock_iam_role, 
                          mock_route_table, mock_general, mock_cluster, mock_diagram):
        # Setup mock context managers
        mock_diagram.return_value.__enter__.return_value = MagicMock()
        mock_cluster.return_value.__enter__.return_value = MagicMock()

        # Call the function
        create_diagram()

        # Verify diagram creation with correct attributes
        mock_diagram.assert_called_once_with(
            "AWS Architecture",
            filename="foo",
            show=False,
            direction="TB",
            graph_attr=graph_attr,
            node_attr=node_attr,
            edge_attr=edge_attr
        )

        # Verify cluster creation for regions
        region_calls = [call for call in mock_cluster.call_args_list 
                       if "Region:" in call[0][0]]
        self.assertEqual(len(region_calls), 2)
        self.assertTrue(any("us-east-1" in call[0][0] for call in region_calls))
        self.assertTrue(any("us-east-2" in call[0][0] for call in region_calls))

        # Verify VPC clusters
        vpc_calls = [call for call in mock_cluster.call_args_list 
                    if "VPC" in call[0][0]]
        self.assertEqual(len(vpc_calls), 2)

        # Verify resource creation
        mock_route_table.assert_called()
        mock_iam_role.assert_called()
        mock_nacl.assert_called()
        mock_fargate.assert_called()

    def test_graph_attributes(self):
        # Test graph attributes are properly defined
        self.assertEqual(graph_attr["splines"], "ortho")
        self.assertEqual(graph_attr["rankdir"], "TB")
        self.assertEqual(graph_attr["layout"], "dot")

    def test_node_attributes(self):
        # Test node attributes are properly defined
        self.assertEqual(node_attr["fontsize"], "12")
        self.assertEqual(node_attr["labelloc"], "b")
        self.assertEqual(node_attr["imagepos"], "tc")

    def test_edge_attributes(self):
        # Test edge attributes are properly defined
        self.assertEqual(edge_attr["minlen"], "2")
        self.assertEqual(edge_attr["penwidth"], "2.0")
        self.assertEqual(edge_attr["color"], "#666666")

if __name__ == '__main__':
    unittest.main()
