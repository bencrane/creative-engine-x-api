from pydantic import BaseModel, ConfigDict


class BrandGuidelines(BaseModel):
    primary_color: str = ""
    secondary_color: str = ""
    accent_color: str = ""
    font_family: str = ""
    logo_url: str = ""
    model_config = ConfigDict(extra="allow")


class ICPDefinition(BaseModel):
    title: str = ""
    industry: str = ""
    company_size: str = ""
    pain_points: list[str] = []
    goals: list[str] = []
    model_config = ConfigDict(extra="allow")


class CaseStudy(BaseModel):
    title: str = ""
    company: str = ""
    result: str = ""
    model_config = ConfigDict(extra="allow")


class Testimonial(BaseModel):
    quote: str = ""
    author: str = ""
    role: str = ""
    company: str = ""
    model_config = ConfigDict(extra="allow")


class BrandContext(BaseModel):
    organization_id: str | None = None
    company_name: str = ""
    industry: str | None = None
    brand_voice: str = ""
    brand_guidelines: BrandGuidelines | None = None
    value_proposition: str = ""
    icp_definition: ICPDefinition | None = None
    target_persona: str = ""
    case_studies: list[CaseStudy] = []
    testimonials: list[Testimonial] = []
    customer_logos: list[str] = []
    competitor_differentiators: list[str] = []
    angle: str | None = None
    objective: str | None = None
    model_config = ConfigDict(extra="allow")
