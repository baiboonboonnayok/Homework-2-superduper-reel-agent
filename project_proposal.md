# MenuMatch AI: An Agentic Restaurant Menu Recommendation Application

## Problem
Restaurant menus are hard to navigate, especially for tourists or first
time customers facing an unfamiliar restaurant, a menu in another
language, or dozens of dishes with no clear standout. Customers often
end up manually searching Google reviews, social media, and food blogs
before deciding what to order, which takes time and often still leaves
them uncertain. Reviews discuss a restaurant generally but rarely make
it obvious which specific dishes are actually worth ordering.

## Audience
Tourists and first time customers at unfamiliar restaurants, people who
find large menus overwhelming, customers who cannot easily read the
menu's language, and anyone who wants a recommendation backed by real
reviews rather than guesswork.

## Scope
We will build an agentic AI application that:
1. Takes a photo of a restaurant menu from the user's phone.
2. Uses OCR and a vision language model to read menu items, prices,
   categories, and dish images.
3. Uses GPS location plus the detected restaurant name to identify the
   exact restaurant and branch.
4. Retrieves publicly available restaurant reviews through permitted
   sources.
5. Matches review mentions, including misspellings, translations, and
   descriptive references, to specific menu items.
6. Runs sentiment analysis on each dish mention to determine positive,
   neutral, or negative reception and the reasons behind it.
7. Ranks dishes using review mention frequency, sentiment ratio,
   recency, signature labeling, and photo frequency.
8. Presents the top recommended appetiser, main dish, signature dish,
   dessert, and drink, each with a plain language explanation and
   supporting review evidence.

## Key Outputs
- Restaurant identification with a confidence score
- Category by category dish recommendations (appetiser, main, signature,
  dessert, drink)
- A short evidence based explanation for every recommendation, grounded
  in real review excerpts
- A popularity and sentiment score per recommended dish
- A like button that stores user feedback to improve future rankings
- Human in the loop prompts when the restaurant or a dish match is
  uncertain

This gives customers, for the first time, a fast and trustworthy answer
to "what should I order here" backed by real reviews instead of guesses.
