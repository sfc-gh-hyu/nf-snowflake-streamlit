
class Config:
    """Configuration class to store key-value pairs with descriptions."""
    
    def __init__(self, key: str, value: str, description: str):
        """
        Initialize a configuration item.
        
        Args:
            key (str): The configuration key/name
            value (str): The configuration value
            description (str): Description of what this configuration represents
        """
        self.key = key
        self.value = value
        self.description = description
    
    def __repr__(self):
        return f"Config(key='{self.key}', value='{self.value}', description='{self.description}')"
    
    def __str__(self):
        return f"{self.key}: {self.value} - {self.description}"


# Configuration instances
NXF_HISTORY_TBL = Config(
    key="NXF_HISTORY_TBL",
    value="NXF_EXECUTION_HISTORY",
    description="Snowflake table used for storing Nextflow pipeline execution history and metadata"
)

NXF_WORKDIR_STAGE = Config(
    key="NXF_WORKDIR_STAGE",
    value="NXF_WORKDIR", 
    description="Snowflake stage used for storing Nextflow intermediate files and artifacts"
)

ALL_CONFIGS = [NXF_HISTORY_TBL, NXF_WORKDIR_STAGE]
