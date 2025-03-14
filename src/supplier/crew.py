from crewai import Agent, Crew, Process, Task,LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, FirecrawlScrapeWebsiteTool, FileWriterTool,EXASearchTool
from dotenv import load_dotenv
from .tools.custom_tool import CombinedTool,SerperSearchTool

load_dotenv()


@CrewBase
class Supplier():
    """AiSuppliers crew"""

    def __init__(self):
        print("AiSuppliers initialized")
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'


    @agent
    def retrieve_suppliers(self) -> Agent:
        return Agent(
            config=self.agents_config['retrieve_suppliers'],
            tools=[SerperSearchTool()],
            verbose=True,
            allow_delegation=True,
        )
    @agent
    def domain_researcher_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['domain_researcher_agent'],
            tools = [CombinedTool(result_as_answer=True)],
            verbose=True,

        )


    @agent
    def ai_suppliers_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['ai_suppliers_writer'],
            verbose=True,

        )



    @task
    def retrieve_suppliers_task(self) -> Task:
        return Task(
            config=self.tasks_config['retrieve_suppliers_task'],
        )

    @task
    def domain_and_trustpilot_researcher_task(self) -> Task:
        return Task(
            config=self.tasks_config['domain_and_trustpilot_researcher_task'],

            # Store the output
        )

    

    @task
    def ai_suppliers_write_task(self) -> Task:
        return Task(
            config=self.tasks_config['ai_suppliers_write_task'],


        )



    @crew
    def crew(self) -> Crew:
        """Creates the AiSuppliers crew"""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            planning=True,
            planning_llm=LLM(
                model = "gemini/gemini-2.0-flash"
			)

            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )