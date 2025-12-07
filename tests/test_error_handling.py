
import unittest
from unittest.mock import MagicMock, patch
from graph import recruit_node, hypothesis_node, debate_node, synthesis_node

class TestErrorHandling(unittest.TestCase):

    @patch('time.sleep', return_value=None)
    @patch('graph.recruit_task')
    @patch('graph.RecruiterAgent')
    @patch('graph.Crew')
    def test_recruit_node_double_failure(self, mock_crew, mock_recruiter, mock_task, mock_sleep):
        # Simulate double failure (primary and fallback)
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        # Primary fail (9 retries) + Fallback fail (9 retries) = 18 calls
        mock_crew_instance.kickoff.side_effect = [Exception("RateLimit")] * 20
        
        state = {'input': 'test problem'}
        # Should not raise exception
        result = recruit_node(state)
        
        # Should contain default experts (3 fallback + 1 AlphaEvolve = 4)
        self.assertEqual(len(result['experts']), 4)
        self.assertEqual(result['experts'][0]['name'], "Expert A")

    @patch('time.sleep', return_value=None)
    @patch('graph.hypothesis_task')
    @patch('graph.create_expert_agent')
    @patch('graph.Crew')
    def test_hypothesis_node_double_failure(self, mock_crew, mock_create, mock_task, mock_sleep):
        import asyncio
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        # Simulate failure
        mock_crew_instance.kickoff.side_effect = [Exception("RateLimit")] * 20
        
        state = {
            'input': 'test',
            'experts': [{'name': 'Alice', 'role': 'R', 'bias': 'B', 'skill': 'S'}]
        }
        
        # Use asyncio.run for async node
        result = asyncio.run(hypothesis_node(state))
        self.assertEqual(len(result['hypotheses']), 1)
        self.assertTrue("Error" in result['hypotheses'][0]['hypothesis'])

    @patch('time.sleep', return_value=None)
    @patch('graph.debate_task')
    @patch('graph.DevilsAdvocate')
    @patch('graph.Crew')
    def test_debate_node_double_failure(self, mock_crew, mock_da, mock_task, mock_sleep):
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        mock_crew_instance.kickoff.side_effect = [Exception("RateLimit")] * 20
        
        state = {'hypotheses': [], 'input': 'test'}
        result = debate_node(state)
        self.assertIn("skipped", result['debate_minutes'])

    @patch('time.sleep', return_value=None)
    @patch('graph.synthesis_task')
    @patch('graph.Synthesizer')
    @patch('graph.Crew')
    def test_synthesis_node_double_failure(self, mock_crew, mock_synth, mock_task, mock_sleep):
        mock_crew_instance = MagicMock()
        mock_crew.return_value = mock_crew_instance
        mock_crew_instance.kickoff.side_effect = [Exception("RateLimit")] * 20
        
        state = {'hypotheses': [], 'debate_minutes': '', 'input': 'test', 'iterations': 0}
        result = synthesis_node(state)
        self.assertIn("skipped", result['final_solution'])

if __name__ == '__main__':
    unittest.main()
