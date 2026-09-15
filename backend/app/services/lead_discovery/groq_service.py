"""Groq API integration service for AI Draft Replies.

Uses Groq API to generate helpful, non-spammy, high-converting social comment/DM replies.
"""
import os
import requests


def generate_draft_reply(post_title, post_content, author="", platform="", subreddit=""):
    """Generate a non-spammy, value-first response to a social post using Groq API.

    :param post_title: Title of the post/result
    :param post_content: Full text or snippet of the post
    :param author: Username of poster
    :param platform: Platform name e.g. "Reddit", "Google Search", "Twitter/X"
    :param subreddit: Subreddit name if applicable e.g. "r/entrepreneur"
    :return: (reply_text, error_string)
    """
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    company_name = os.getenv("COMPANY_NAME", "Ascentra Global")

    if not groq_api_key:
        return None, "Groq AI Reply Drafter is unavailable: environment variable GROQ_API_KEY is not set."

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json",
    }

    platform_info = f"on {platform}" if platform else ""
    if subreddit:
        platform_info += f" ({subreddit})"

    system_prompt = (
        f"You are an expert technical consultant representing '{company_name}'. "
        f"Your task is to write a helpful, non-spammy, highly authentic comment or direct message response "
        f"to a potential client posting {platform_info}.\n\n"
        f"RULES FOR REPLIES:\n"
        f"1. Be extremely helpful FIRST: Give 2-3 concrete, actionable insights, answers, or suggestions directly relevant to their problem.\n"
        f"2. Never use robotic hype, generic buzzwords, or hard-sell pressure tactics.\n"
        f"3. Maintain a warm, peer-to-peer developer/agency founder tone.\n"
        f"4. End with a subtle, friendly note offering further help or a quick chat from {company_name}.\n"
        f"5. Keep the response under 180 words, perfectly formatted for a post reply."
    )

    user_prompt = (
        f"POST DETAILS:\n"
        f"- Title: {post_title}\n"
        f"- Author: {author or 'User'}\n"
        f"- Platform/Context: {platform_info}\n"
        f"- Content:\n{post_content}\n\n"
        f"Write the response now."
    )

    payload = {
        "model": groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 400,
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15)
        if res.status_code != 200:
            err_msg = f"Groq API returned HTTP {res.status_code}."
            try:
                err_data = res.json().get("error", {})
                if err_data.get("message"):
                    err_msg += f" {err_data['message']}"
            except Exception:
                pass
            return None, err_msg

        data = res.json()
        choices = data.get("choices", [])
        if choices and "message" in choices[0]:
            reply = choices[0]["message"].get("content", "").strip()
            return reply, None
        return None, "No completion choice returned from Groq API."

    except Exception as exc:
        return None, f"Groq API call failed: {str(exc)}"
