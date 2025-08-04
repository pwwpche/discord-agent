def get_prompt(thread_link: str) -> str:
    return f"""
**ROLE:**
You are an expert community discussion analyst. Your task is to process a long Discord thread and create a structured report that will allow a community member to quickly catch up and participate constructively.

**CONTEXT:**
I am a member of a community, and I need to understand a long-running discussion in a Discord thread with lots of messages. My goal is to grasp the conversation's history, the different viewpoints, the current consensus, and any unresolved questions so I can contribute effectively without asking things that have already been answered.

**TASK:**
Analyze the following Discord thread transcript and generate a report with the following sections. Please be objective, neutral, and focus on the substance of the discussion, ignoring off-topic chatter, spam, and simple "lol" or "agree" type messages.

**OUTPUT STRUCTURE:**

**1. Executive Summary (TL;DR):**
A brief, 3-4 sentence paragraph summarizing the core topic of the discussion and the general outcome or current state.

**2. Timeline of Key Developments:**
A chronological, bulleted list of how the conversation evolved. For example:
*   [Date/Timeframe] The discussion began with a proposal by [User] about [Topic].
*   [Date/Timeframe] A major counter-argument or concern was raised by [User] regarding [Issue].
*   [Date/Timeframe] The focus shifted to discussing alternative solutions, such as [Alternative Idea].
*   [Date/Timeframe] A rough consensus started to form around [Specific Point].

**3. Key Participants and Their Stances:**
A list of the most active/influential participants and a brief, neutral summary of their primary viewpoint, arguments, or role in the conversation.
*   **[Username 1]:** (e.g., The original proposer) Argued for [X] because of [Y].
*   **[Username 2]:** (e.g., The main critic) Raised concerns about [A], [B], and [C].
*   **[Username 3]:** (e.g., The mediator/solution-builder) Suggested a compromise that combined ideas from others.

**4. Main Areas of Agreement (Consensus):**
A bulleted list of points, ideas, or conclusions that most participants seem to agree on.

**5. Main Areas of Disagreement (Contention):**
A bulleted list of the key sticking points, unresolved debates, or topics where there are clear opposing views.

**6. Current Status & Open Questions:**
A final summary of where the conversation currently stands. End with a bulleted list of the most important open questions or proposed next steps that I could help with.
*   What is the final decision on [X]?
*   Who is responsible for implementing [Y]?
*   Is proposal [Z] still being considered?

**PLease fetch the thread transcript from the following link, using related tools.**
{thread_link}
    """