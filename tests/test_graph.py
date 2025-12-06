import unittest
from unittest.mock import MagicMock, patch
import json
from graph import recruit_node, hypothesis_node, debate_node, synthesis_node, check_confidence

class TestGraph(unittest.TestCase):

    @patch('graph.recruit_task')
    @patch('graph.RecruiterAgent')
    @patch('graph.Crew')
    def test_recruit_node(self, mock_crew, mock_recruiter, mock_task):
        # Setup mocks
        mock_agent = MagicMock()
        mock_recruiter.return_value.recruit.return_value = mock_agent
        
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        
        # Simulate successful JSON output
        expected_experts = [
            {"name": "Alice", "role": "Physicist", "bias": "Theoretical", "skill": "Quantum Mechanics"},
            {"name": "Bob", "role": "Engineer", "bias": "Practical", "skill": "Robotics"}
        ]
        # Simulate successful JSON output via CrewOutput object
        mock_output = MagicMock()
        mock_output.json_dict = {"experts": expected_experts}
        mock_output.pydantic = None
        mock_crew_instance.kickoff.return_value = mock_output
        
        state = {'input': 'test problem'}
        result = recruit_node(state)
        
        # The graph now adds AlphaEvolve systematically
        self.assertEqual(len(result['experts']), 3) 
        self.assertEqual(result['experts'][0], expected_experts[0])
        self.assertEqual(result['experts'][1], expected_experts[1])
        self.assertEqual(result['experts'][2]['name'], "AlphaEvolve")
        self.assertEqual(result['iterations'], 0)

    @patch('graph.recruit_task')
    @patch('graph.RecruiterAgent')
    @patch('graph.Crew')
    def test_recruit_node_failure(self, mock_crew, mock_recruiter, mock_task):
        # Setup mocks
        mock_agent = MagicMock()
        mock_recruiter.return_value.recruit.return_value = mock_agent
        
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        
        # Simulate bad output
        mock_crew_instance.kickoff.return_value = "Not JSON"
        
        state = {'input': 'test problem'}
        result = recruit_node(state)
        
        # Should return fallback experts
        # Should return fallback experts + AlphaEvolve = 4
        self.assertEqual(len(result['experts']), 4)
        self.assertEqual(result['experts'][0]['name'], "Expert A")

    @patch('graph.hypothesis_task')
    @patch('graph.create_expert_agent')
    @patch('graph.Crew')
    def test_hypothesis_node(self, mock_crew, mock_create_expert, mock_task):
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        mock_crew_instance.kickoff.return_value = "Hypothesis content"
        
        state = {
            'input': 'test',
            'experts': [{'name': 'Alice', 'role': 'R', 'bias': 'B', 'skill': 'S'}]
        }
        
        result = hypothesis_node(state)
        
        self.assertEqual(len(result['hypotheses']), 1)
        self.assertEqual(result['hypotheses'][0]['expert_name'], 'Alice')
        self.assertEqual(result['hypotheses'][0]['hypothesis'], "Hypothesis content")

    @patch('graph.debate_task')
    @patch('graph.DevilsAdvocate')
    @patch('graph.Crew')
    def test_debate_node(self, mock_crew, mock_devils_advocate, mock_task):
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        mock_crew_instance.kickoff.return_value = "Debate minutes"
        
        state = {
            'input': 'test',
            'hypotheses': []
        }
        
        result = debate_node(state)
        self.assertEqual(result['debate_minutes'], "Debate minutes")

    @patch('graph.synthesis_task')
    @patch('graph.Synthesizer')
    @patch('graph.Crew')
    def test_synthesis_node(self, mock_crew, mock_synthesizer, mock_task):
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        # Simulate output with confidence score
        mock_crew_instance.kickoff.return_value = "Solution... Confidence Score: 85.5"
        
        state = {
            'input': 'test',
            'debate_minutes': 'minutes',
            'hypotheses': [],
            'iterations': 0
        }
        
        result = synthesis_node(state)
        
        self.assertEqual(result['confidence_score'], 85.5)
        self.assertEqual(result['iterations'], 1)

    def test_check_confidence(self):
        # Test end condition (high confidence)
        state = {'confidence_score': 100, 'iterations': 1}
        self.assertEqual(check_confidence(state), "end")
        
        # Test end condition (max iterations)
        state = {'confidence_score': 50, 'iterations': 3}
        self.assertEqual(check_confidence(state), "end")
        
        # Test loop condition
        state = {'confidence_score': 50, 'iterations': 1}
        self.assertEqual(check_confidence(state), "loop")

if __name__ == '__main__':
    unittest.main()
