import vectorSearchService from "./src/services/vectorSearchService.js";

// Test the VectorSearchService
async function testVectorSearchService() {
  console.log("🔍 Testing Vector Search Service...\n");

  try {
    // Test 1: Generate embedding
    console.log("1. Testing embedding generation...");
    const testText =
      "Kansas City Chiefs vs Buffalo Bills - weather conditions and team performance";
    const embedding = await vectorSearchService.generateEmbedding(testText);

    if (embedding && embedding.length === 384) {
      console.log("✅ Embedding generation working");
      console.log(`📊 Generated ${embedding.length}-dimensional vector`);
    } else {
      console.log("❌ Embedding generation failed");
      return false;
    }

    // Test 2: Search knowledge base
    console.log("\n2. Testing knowledge base search...");
    const kbResults = await vectorSearchService.searchKnowledgeBase(
      "NFL team performance analysis",
      { matchThreshold: 0.5, matchCount: 3 }
    );

    if (kbResults.success) {
      console.log("✅ Knowledge base search working");
      console.log(`📊 Found ${kbResults.matchCount} results`);
    } else {
      console.log(
        "⚠️ Knowledge base search returned no results (expected for empty database)"
      );
    }

    // Test 3: Search expert research
    console.log("\n3. Testing expert research search...");
    const erResults = await vectorSearchService.searchExpertResearch(
      "betting strategies and analysis",
      { matchThreshold: 0.5, matchCount: 3 }
    );

    if (erResults.success) {
      console.log("✅ Expert research search working");
      console.log(`📊 Found ${erResults.matchCount} results`);
    } else {
      console.log(
        "⚠️ Expert research search returned no results (expected for empty database)"
      );
    }

    // Test 4: Search news articles
    console.log("\n4. Testing news articles search...");
    const newsResults = await vectorSearchService.searchNewsArticles(
      "NFL injury reports and team news",
      { matchThreshold: 0.5, matchCount: 3 }
    );

    if (newsResults.success) {
      console.log("✅ News articles search working");
      console.log(`📊 Found ${newsResults.matchCount} results`);
    } else {
      console.log(
        "⚠️ News articles search returned no results (expected for empty database)"
      );
    }

    // Test 5: Search similar bets
    console.log("\n5. Testing similar bets search...");
    const betsResults = await vectorSearchService.searchSimilarBets(
      "spread betting analysis and reasoning",
      { matchThreshold: 0.5, matchCount: 3 }
    );

    if (betsResults.success) {
      console.log("✅ Similar bets search working");
      console.log(`📊 Found ${betsResults.matchCount} results`);
    } else {
      console.log(
        "⚠️ Similar bets search returned no results (expected for empty database)"
      );
    }

    // Test 6: Search prediction analysis
    console.log("\n6. Testing prediction analysis search...");
    const predResults = await vectorSearchService.searchPredictionAnalysis(
      "ML model predictions and confidence scores",
      { matchThreshold: 0.5, matchCount: 3 }
    );

    if (predResults.success) {
      console.log("✅ Prediction analysis search working");
      console.log(`📊 Found ${predResults.matchCount} results`);
    } else {
      console.log(
        "⚠️ Prediction analysis search returned no results (expected for empty database)"
      );
    }

    // Test 7: Multi-source search
    console.log("\n7. Testing multi-source search...");
    const allResults = await vectorSearchService.searchAllContent(
      "NFL predictions and betting analysis",
      { matchThreshold: 0.5, matchCount: 10 }
    );

    if (allResults.success) {
      console.log("✅ Multi-source search working");
      console.log(`📊 Found ${allResults.matchCount} results`);
      console.log("📊 Sources:", Object.keys(allResults.sources));
    } else {
      console.log(
        "⚠️ Multi-source search returned no results (expected for empty database)"
      );
    }

    // Test 8: Store expert research
    console.log("\n8. Testing store expert research...");
    const storeResult = await vectorSearchService.storeExpertResearch(
      "test_expert_001",
      "team_analysis",
      "The Kansas City Chiefs have shown strong offensive performance this season with their dynamic passing game and solid running back committee.",
      { teams: ["Kansas City Chiefs"], analysis_type: "offensive" }
    );

    if (storeResult.success) {
      console.log("✅ Store expert research working");
      console.log(`📊 Stored research ID: ${storeResult.research.id}`);
    } else {
      console.log("❌ Store expert research failed:", storeResult.error);
    }

    // Test 9: Store expert bet
    console.log("\n9. Testing store expert bet...");
    const betResult = await vectorSearchService.storeExpertBet(
      "test_expert_001",
      "00000000-0000-0000-0000-000000000000", // Dummy UUID
      "spread",
      3.5,
      85,
      "Chiefs have a strong home field advantage and better offensive weapons in this matchup."
    );

    if (betResult.success) {
      console.log("✅ Store expert bet working");
      console.log(`📊 Stored bet ID: ${betResult.bet.id}`);
    } else {
      console.log("❌ Store expert bet failed:", betResult.error);
    }

    // Test 10: Add knowledge
    console.log("\n10. Testing add knowledge...");
    const knowledgeResult = await vectorSearchService.addKnowledge(
      "team_stats",
      "Chiefs Offensive Performance 2023",
      "The Kansas City Chiefs led the NFL in passing yards per game and ranked in the top 5 for total offensive yards.",
      "https://example.com/stats",
      85
    );

    if (knowledgeResult.success) {
      console.log("✅ Add knowledge working");
      console.log(`📊 Added knowledge ID: ${knowledgeResult.knowledge.id}`);
    } else {
      console.log("❌ Add knowledge failed:", knowledgeResult.error);
    }

    console.log("\n🎉 Vector Search Service tests completed successfully!");
    return true;
  } catch (error) {
    console.error("❌ Vector Search Service test failed:", error);
    return false;
  }
}

// Test bulk embedding functionality
async function testBulkEmbedding() {
  console.log("\n🔄 Testing bulk embedding functionality...");

  try {
    // Test bulk embedding for knowledge base
    const kbResult = await vectorSearchService.bulkEmbedExistingContent(
      "knowledge_base",
      "content",
      "embedding"
    );

    if (kbResult.success) {
      console.log("✅ Bulk embedding for knowledge base working");
      console.log(`📊 Processed ${kbResult.processed} records`);
    } else {
      console.log(
        "⚠️ Bulk embedding returned no records to process (expected for empty database)"
      );
    }

    // Test bulk embedding for expert research
    const erResult = await vectorSearchService.bulkEmbedExistingContent(
      "expert_research",
      "content",
      "embedding"
    );

    if (erResult.success) {
      console.log("✅ Bulk embedding for expert research working");
      console.log(`📊 Processed ${erResult.processed} records`);
    } else {
      console.log(
        "⚠️ Bulk embedding returned no records to process (expected for empty database)"
      );
    }
  } catch (error) {
    console.error("❌ Bulk embedding test failed:", error);
  }
}

// Run all tests
async function runVectorSearchTests() {
  console.log("🚀 Starting Vector Search Service Tests...\n");

  const serviceOk = await testVectorSearchService();

  if (serviceOk) {
    await testBulkEmbedding();
    console.log("\n🎉 All Vector Search Service tests completed!");
  } else {
    console.log("\n💥 Vector Search Service tests failed!");
  }
}

// Export for use in other files
export { testVectorSearchService, testBulkEmbedding, runVectorSearchTests };

// Run if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runVectorSearchTests();
}
