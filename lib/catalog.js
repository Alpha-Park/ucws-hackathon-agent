import { PRODUCTS } from "./products.js";

const CATEGORY_KEYWORDS = {
  "AI Gadgets": new Set(["ai", "assistant", "speaker", "voice", "gadget", "smart"]),
  Electronics: new Set(["electronics", "charger", "audio", "earbuds", "wireless", "battery", "tech"]),
  "Home & Living": new Set(["home", "desk", "chair", "office", "vacuum", "cleaning", "living"]),
  "Pet Supplies": new Set(["pet", "pets", "dog", "cat", "feeder"]),
  Fashion: new Set(["fashion", "wallet", "leather", "style", "rfid"]),
  Lifestyle: new Set(["lifestyle", "garden", "plants", "indoor", "eco", "wellness"]),
};

const STOP_WORDS = new Set([
  "a",
  "an",
  "and",
  "are",
  "as",
  "at",
  "best",
  "buy",
  "can",
  "circle",
  "community",
  "compare",
  "draft",
  "for",
  "find",
  "gift",
  "globally",
  "help",
  "i",
  "in",
  "is",
  "me",
  "of",
  "on",
  "or",
  "please",
  "post",
  "product",
  "products",
  "recommend",
  "save",
  "show",
  "shortlist",
  "some",
  "that",
  "the",
  "to",
  "under",
  "with",
  "within",
  "useful",
]);

export function inferBudget(text) {
  const patterns = [
    /(?:under|below|less than|max|maximum|budget|within)\s*\$?\s*(\d+(?:\.\d+)?)/i,
    /\$\s*(\d+(?:\.\d+)?)/i,
    /(\d+(?:\.\d+)?)\s*(?:usd|dollars|sgd)/i,
  ];

  for (const pattern of patterns) {
    const match = pattern.exec(text);
    if (match) return Number.parseFloat(match[1]);
  }

  return null;
}

export function tokenize(text) {
  return Array.from(String(text).toLowerCase().matchAll(/[a-z0-9]+/g))
    .map((match) => match[0])
    .filter((token) => token.length > 1 && !STOP_WORDS.has(token));
}

export function inferCategory(text) {
  const words = new Set(tokenize(text));
  let bestCategory = null;
  let bestScore = 0;

  for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    let score = 0;
    for (const word of words) {
      if (keywords.has(word)) score += 1;
    }
    if (score > bestScore) {
      bestCategory = category;
      bestScore = score;
    }
  }

  return bestCategory;
}

function productText(product) {
  return `${product.name} ${product.category} ${product.description} ${product.tags.join(" ")}`.toLowerCase();
}

export function rankProducts(query, { category = null, maxPrice = null, limit = 5 } = {}) {
  const tokens = tokenize(query);
  const ranked = [];

  for (const product of PRODUCTS) {
    if (category && product.category.toLowerCase() !== category.toLowerCase()) continue;
    if (maxPrice !== null && product.price > maxPrice) continue;

    const haystack = productText(product);
    let score = product.rating / 5;
    const matchedTerms = [];

    for (const token of tokens) {
      if (haystack.includes(token)) {
        score += 1;
        matchedTerms.push(token);
      }
    }

    if (category && product.category.toLowerCase() === category.toLowerCase()) {
      score += 0.75;
    }

    if (maxPrice !== null) {
      const headroom = maxPrice - product.price;
      if (headroom >= 0) score += Math.min(headroom / maxPrice, 0.15);
    }

    if (score > 0) {
      ranked.push([
        score,
        {
          ...product,
          match_score: Number(score.toFixed(3)),
          why: buildReason(product, matchedTerms, maxPrice),
        },
      ]);
    }
  }

  return ranked
    .sort((a, b) => b[0] - a[0])
    .slice(0, limit)
    .map(([, product]) => product);
}

function buildReason(product, matchedTerms, maxPrice) {
  const reasons = [];
  const uniqueTerms = Array.from(new Set(matchedTerms)).sort();

  if (uniqueTerms.length) reasons.push(`matches ${uniqueTerms.join(", ")}`);
  if (maxPrice !== null && product.price <= maxPrice) reasons.push(`fits the $${maxPrice} budget`);
  reasons.push(`rated ${product.rating}/5`);

  return reasons.join("; ");
}

export function summarizeProducts(products) {
  if (!products.length) return "I could not find a strong product match yet.";

  return products
    .map((product, index) => {
      const reason = product.why || product.description;
      return `${index + 1}. ${product.name} ($${product.price.toFixed(2)}) - ${reason}`;
    })
    .join("\n");
}
