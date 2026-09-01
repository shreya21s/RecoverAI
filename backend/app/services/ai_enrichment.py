import logging
from app.config import settings

logger = logging.getLogger("recoverai.ai_enrichment")

class AIEnrichmentService:
    def __init__(self):
        self.ai_enabled = (
            settings.AI_PROVIDER is not None and 
            settings.AI_PROVIDER.strip() != "" and 
            settings.AI_API_KEY is not None and 
            settings.AI_API_KEY.strip() != ""
        )
        if self.ai_enabled:
            logger.info(f"AI Enrichment enabled. Provider: {settings.AI_PROVIDER}")
        else:
            logger.info("AI Enrichment disabled. Using deterministic fallbacks.")

    def get_diagnosis_summary(self, failure_category: str, confidence: float, evidence: list) -> str:
        if not self.ai_enabled:
            return self._fallback_diagnosis(failure_category, confidence, evidence)
        
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            
            model_name = settings.AI_MODEL or "gemini-2.5-flash"
            llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=settings.AI_API_KEY)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a payment recovery analysis assistant.\n"
                    "Analyze the supplied structured payment failure details and write a concise, professional one-sentence business summary explanation of why it failed.\n"
                    "Do not invent facts, customer details, or payment history.\n"
                    "Keep summaries under 20 words."
                )),
                ("user", "Failure Category: {category}\nConfidence: {confidence}\nEvidence: {evidence}")
            ])
            
            chain = prompt | llm
            res = chain.invoke({
                "category": failure_category,
                "confidence": confidence,
                "evidence": ", ".join(evidence)
            })
            return res.content.strip()
        except Exception as e:
            logger.error(f"AI diagnosis summary generation failed: {e}. Falling back to deterministic template.")
            return self._fallback_diagnosis(failure_category, confidence, evidence)

    def get_customer_summary(self, segment: str, quality_score: float, reliability: float, engagement: float) -> str:
        if not self.ai_enabled:
            return self._fallback_customer(segment, quality_score, reliability, engagement)
            
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            
            model_name = settings.AI_MODEL or "gemini-2.5-flash"
            llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=settings.AI_API_KEY)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a payment recovery customer profiling assistant.\n"
                    "Analyze the customer's payment metrics and segment, and write a concise, professional one-sentence business summary of their profile.\n"
                    "Do not invent facts, scores, or names.\n"
                    "Keep summaries under 20 words."
                )),
                ("user", "Segment: {segment}\nQuality Score: {quality}\nReliability: {reliability}\nEngagement Score: {engagement}")
            ])
            
            chain = prompt | llm
            res = chain.invoke({
                "segment": segment,
                "quality": quality_score,
                "reliability": reliability,
                "engagement": engagement
            })
            return res.content.strip()
        except Exception as e:
            logger.error(f"AI customer summary generation failed: {e}. Falling back to deterministic template.")
            return self._fallback_customer(segment, quality_score, reliability, engagement)

    def get_strategy_summary(self, recommended_action: str, probability: float, expected_value: float, cost: float) -> str:
        if not self.ai_enabled:
            return self._fallback_strategy(recommended_action, probability, expected_value, cost)
            
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.prompts import ChatPromptTemplate
            
            model_name = settings.AI_MODEL or "gemini-2.5-flash"
            llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=settings.AI_API_KEY)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are a payment recovery strategy planning assistant.\n"
                    "Analyze the recommended action and strategy metrics, and write a concise, professional one-sentence business summary explaining the rationale.\n"
                    "Do not invent strategies, cost, or expected values.\n"
                    "Keep summaries under 20 words."
                )),
                ("user", "Recommended Action: {action}\nRecovery Probability: {prob}\nExpected Recovery Value: {val}\nAction Cost: {cost}")
            ])
            
            chain = prompt | llm
            res = chain.invoke({
                "action": recommended_action,
                "prob": probability,
                "val": expected_value,
                "cost": cost
            })
            return res.content.strip()
        except Exception as e:
            logger.error(f"AI strategy summary generation failed: {e}. Falling back to deterministic template.")
            return self._fallback_strategy(recommended_action, probability, expected_value, cost)

    def _fallback_diagnosis(self, failure_category: str, confidence: float, evidence: list) -> str:
        evidence_str = ", ".join(evidence) if evidence else "No diagnostic evidence provided."
        return f"Diagnosed payment failure as {failure_category} (confidence: {confidence:.0%}) due to: {evidence_str}."

    def _fallback_customer(self, segment: str, quality_score: float, reliability: float, engagement: float) -> str:
        return f"Customer classified as {segment} segment. Quality score: {quality_score:.2f}, Reliability: {reliability:.1%}, Engagement: {engagement:.1%}."

    def _fallback_strategy(self, recommended_action: str, probability: float, expected_value: float, cost: float) -> str:
        return f"Recommended action is {recommended_action} (recovery probability: {probability:.1%}, expected recovery value: Rs. {expected_value:.2f}, action cost: Rs. {cost:.2f})."
