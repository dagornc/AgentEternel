from pydantic import BaseModel, Field
from typing import List

class Expert(BaseModel):
    name: str = Field(..., description="The name of the expert")
    role: str = Field(..., description="The role of the expert (e.g., Biologist)")
    bias: str = Field(..., description="The bias of the expert")
    skill: str = Field(..., description="The signature skill of the expert")
    backstory: str = Field(..., description="A brief backstory for the expert")

class ExpertList(BaseModel):
    experts: List[Expert]

class SynthesisReport(BaseModel):
    solution: str = Field(..., description="The unified solution synthesized from the debate.")
    confidence_score: float = Field(..., description="A confidence score between 0 and 100.")
    knowledge_gaps: List[str] = Field(default_factory=list, description="List of specific knowledge gaps or missing data preventing a higher score.")
    visualization_code: str = Field(default="", description="Mermaid.js code representing the concepts and their relationships.")
