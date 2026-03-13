"""Reusable prompt components: Roles, Rules, and OutputRules."""

from ai_pipeline_core import OutputRule, Role, Rule


class BlockchainResearcher(Role):
    """Web-research role for blockchain/DeFi analysis."""

    text = "experienced blockchain researcher specializing in cross-chain token analysis and DeFi protocol security"


class TechnicalDocumentWriter(Role):
    """Formatting and consolidation role."""

    text = "technical documentation writer who produces structured, precise documents from raw data sources"


class SecurityAnalyst(Role):
    """Final report generation role."""

    text = (
        "senior blockchain security analyst with deep expertise in "
        "cross-chain risk assessment, bridge security, and smart contract auditing"
    )


class NoInformationLoss(Rule):
    """Data consolidation constraint."""

    text = (
        "Do not omit, summarize, or filter any data from the input sources. "
        "Every data point must appear in the output."
    )


class CiteExactAddresses(Rule):
    """Address fidelity constraint."""

    text = (
        "Reproduce all contract addresses and transaction hashes exactly as provided. "
        "Never abbreviate, truncate, or modify hex strings."
    )


class CiteWebSources(Rule):
    """Source attribution constraint."""

    text = (
        "For every claim based on web research, cite the specific source URL or "
        "document name where the information was found."
    )


class PreserveNegativeResults(Rule):
    """Negative result handling."""

    text = (
        "When no results are found for a search scope, explicitly state "
        "'No results found for [scope]' rather than omitting the scope silently."
    )


class MarkdownOutput(OutputRule):
    """Standard output format."""

    text = (
        "Output must be valid Markdown. Use tables for structured comparative data, "
        "headers for sections, and code blocks for addresses."
    )


class StructuredTableOutput(OutputRule):
    """Table-heavy output format."""

    text = (
        "Present deployment lists, bridge routes, and audit findings in Markdown tables "
        "with consistent column headers."
    )
