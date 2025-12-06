import unittest
from visualization import update_graph_state

class TestVisualization(unittest.TestCase):

    def setUp(self):
        self.nodes = [{"id": "Recruiter", "label": "Chief of Staff"}]
        self.edges = []

    def test_recruit_step(self):
        key = "recruit"
        value = {
            'experts': [
                {'name': 'Alice', 'role': 'Physicist', 'skill': 'Quantum', 'backstory': 'Backstory A', 'bias': 'Bias A'},
                {'name': 'Bob', 'role': 'Engineer', 'skill': 'Robotics', 'backstory': 'Backstory B', 'bias': 'Bias B'}
            ]
        }
        
        nodes, edges = update_graph_state(key, value, self.nodes, self.edges)
        
        # Check nodes
        self.assertEqual(len(nodes), 4) # Recruiter + Cluster + Alice + Bob
        self.assertTrue(any(n['id'] == 'Alice' for n in nodes))
        self.assertTrue(any(n['id'] == 'Bob' for n in nodes))
        
        # Check edges
        self.assertEqual(len(edges), 2)
        self.assertTrue(any(e['source'] == 'Recruiter' and e['target'] == 'Alice' for e in edges))
        self.assertTrue(any(e['source'] == 'Recruiter' and e['target'] == 'Bob' for e in edges))

    def test_hypothesis_step(self):
        # Setup experts first (simulating recruit output)
        self.nodes.append({"id": "cluster_experts", "isCluster": True})
        self.nodes.append({"id": "Alice", "parent": "cluster_experts", "meta_name": "Alice"})
        self.nodes.append({"id": "Bob", "parent": "cluster_experts", "meta_name": "Bob"})
        
        key = "hypothesis"
        value = {
            'hypotheses': [
                {'expert_name': 'Alice', 'hypothesis': 'H1'},
                {'expert_name': 'Bob', 'hypothesis': 'H2'}
            ]
        }
        
        nodes, edges = update_graph_state(key, value, self.nodes, self.edges)
        
        # Check visuals - Alice should be active
        alice = next(n for n in nodes if n['id'] == "Alice")
        self.assertIn("active-node", alice.get('cssClass', ''))
        
        # Check Devil's Advocate node is NOT yet created (created in debate)
        self.assertFalse(any(n['id'] == 'DevilsAdvocate' for n in nodes))

    def test_debate_step(self):
        # Setup DA node
        self.nodes.append({"id": "DevilsAdvocate"})
        
        key = "debate"
        value = {'debate_minutes': 'minutes'}
        
        nodes, edges = update_graph_state(key, value, self.nodes, self.edges)
        
        # Check DA node is still there and active
        self.assertTrue(any(n['id'] == 'DevilsAdvocate' for n in nodes))
        da = next(n for n in nodes if n['id'] == "DevilsAdvocate")
        self.assertIn("active-node", da.get('cssClass', ''))
        
        # Synthesizer is NOT yet created (created in synthesis)
        self.assertFalse(any(n['id'] == 'Synthesizer' for n in nodes))

if __name__ == '__main__':
    unittest.main()
