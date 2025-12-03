# meeting_extractor/crew.py
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class MeetingExtractor():
    """Meeting Action-Item Extractor crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def ingestor(self) -> Agent:
        return Agent(
            config=self.agents_config['ingestor'],
            verbose=True
        )

    @agent
    def action_finder(self) -> Agent:
        return Agent(
            config=self.agents_config['action_finder'],
            verbose=True
        )

    @agent
    def prioritizer(self) -> Agent:
        return Agent(
            config=self.agents_config['prioritizer'],
            verbose=True
        )

    @agent
    def formatter(self) -> Agent:
        return Agent(
            config=self.agents_config['formatter'],
            verbose=True
        )

    @task
    def parse_transcript(self) -> Task:
        return Task(config=self.tasks_config['parse_transcript'])

    @task
    def find_actions(self) -> Task:
        return Task(config=self.tasks_config['find_actions'])

    @task
    def prioritize_actions(self) -> Task:
        return Task(config=self.tasks_config['prioritize_actions'])

    @task
    def format_output(self) -> Task:
        return Task(config=self.tasks_config['format_output'],
                    output_file='output/report.md')

    @crew
    def crew(self) -> Crew:
        """Creates the MeetingExtractor crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
