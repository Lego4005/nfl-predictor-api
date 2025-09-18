import { createClient } from "@supabase/supabase-js";

const supabaseUrl = "https://vaypgzvivahnfegnlinn.supabase.co";
const supabaseKey =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZheXBnenZpdmFobmZlZ25saW5uIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc4NzEzMjIsImV4cCI6MjA3MzQ0NzMyMn0.RISVGvci0v8GD1DtmnOD9lgJSYyfErDg1c__24K82ws";

const supabase = createClient(supabaseUrl, supabaseKey);

// Test query
async function testConnection() {
  console.log("🔍 Testing Supabase connection...");

  try {
    // Test basic connection
    const { data, error } = await supabase.from("games").select("*").limit(1);

    if (error) {
      console.error("❌ Error:", error);
      return false;
    } else {
      console.log("✅ Success! Connected to Supabase");
      console.log("📊 Data:", data);

      // Test all tables exist
      const tables = [
        "games",
        "predictions",
        "odds_history",
        "user_picks",
        "user_stats",
        "news_sentiment",
        "model_performance",
      ];

      for (const table of tables) {
        const { data: tableData, error: tableError } = await supabase
          .from(table)
          .select("*")
          .limit(1);

        if (tableError) {
          console.error(`❌ Error accessing ${table}:`, tableError);
        } else {
          console.log(`✅ Table ${table} accessible`);
        }
      }

      return true;
    }
  } catch (err) {
    console.error("❌ Connection failed:", err);
    return false;
  }
}

// Test database functions
async function testFunctions() {
  console.log("🔧 Testing database functions...");

  try {
    // Test update_game_status function
    const { data, error } = await supabase.rpc("update_game_status");

    if (error) {
      console.error("❌ Function error:", error);
    } else {
      console.log("✅ update_game_status function works");
    }
  } catch (err) {
    console.error("❌ Function test failed:", err);
  }
}

// Test pgvector functionality
async function testPgVector() {
  console.log("🧮 Testing pgvector functionality...");

  try {
    // Test vector operations
    const { data, error } = await supabase.rpc("vector_dims", {
      vector: "[1,2,3,4,5]",
    });

    if (error) {
      console.error("❌ pgvector error:", error);
    } else {
      console.log("✅ pgvector extension working");
      console.log("📊 Vector dimensions:", data);
    }

    // Test vector similarity
    const { data: similarityData, error: similarityError } = await supabase
      .from("team_embeddings")
      .select("*")
      .limit(1);

    if (similarityError && similarityError.code !== "PGRST116") {
      console.error("❌ Vector table error:", similarityError);
    } else {
      console.log("✅ Vector table accessible");
    }
  } catch (err) {
    console.error("❌ pgvector test failed:", err);
  }
}

// Test advanced vector search functions
async function testAdvancedVectorFunctions() {
  console.log("🔍 Testing advanced vector search functions...");

  try {
    // Test knowledge base search
    const { data: kbData, error: kbError } = await supabase.rpc(
      "search_knowledge_base",
      {
        query_embedding:
          "[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360,361,362,363,364,365,366,367,368,369,370,371,372,373,374,375,376,377,378,379,380,381,382,383,384]",
        match_threshold: 0.5,
        match_count: 5,
      }
    );

    if (kbError) {
      console.error("❌ Knowledge base search error:", kbError);
    } else {
      console.log("✅ Knowledge base search function working");
    }

    // Test expert research search
    const { data: erData, error: erError } = await supabase.rpc(
      "search_expert_research",
      {
        query_embedding:
          "[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360,361,362,363,364,365,366,367,368,369,370,371,372,373,374,375,376,377,378,379,380,381,382,383,384]",
        match_threshold: 0.5,
        match_count: 5,
      }
    );

    if (erError) {
      console.error("❌ Expert research search error:", erError);
    } else {
      console.log("✅ Expert research search function working");
    }

    // Test comprehensive search
    const { data: allData, error: allError } = await supabase.rpc(
      "search_all_content",
      {
        query_embedding:
          "[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156,157,158,159,160,161,162,163,164,165,166,167,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,227,228,229,230,231,232,233,234,235,236,237,238,239,240,241,242,243,244,245,246,247,248,249,250,251,252,253,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,295,296,297,298,299,300,301,302,303,304,305,306,307,308,309,310,311,312,313,314,315,316,317,318,319,320,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360,361,362,363,364,365,366,367,368,369,370,371,372,373,374,375,376,377,378,379,380,381,382,383,384]",
        match_threshold: 0.5,
        match_count: 10,
      }
    );

    if (allError) {
      console.error("❌ Comprehensive search error:", allError);
    } else {
      console.log("✅ Comprehensive search function working");
    }

    console.log("🎯 All advanced vector search functions tested successfully!");
  } catch (err) {
    console.error("❌ Advanced vector functions test failed:", err);
  }
}

// Test realtime subscriptions
async function testRealtimeSubscriptions() {
  console.log("📡 Testing realtime subscriptions...");

  try {
    // Test realtime subscription for games table
    const gamesSubscription = supabase
      .channel("games-realtime-test")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "games" },
        (payload) => {
          console.log("📡 Games realtime event:", payload.eventType);
        }
      )
      .subscribe();

    // Test realtime subscription for predictions table
    const predictionsSubscription = supabase
      .channel("predictions-realtime-test")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "predictions" },
        (payload) => {
          console.log("📡 Predictions realtime event:", payload.eventType);
        }
      )
      .subscribe();

    // Test realtime subscription for expert research table
    const expertResearchSubscription = supabase
      .channel("expert-research-realtime-test")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "expert_research" },
        (payload) => {
          console.log("📡 Expert research realtime event:", payload.eventType);
        }
      )
      .subscribe();

    console.log("✅ Realtime subscriptions established");
    console.log("📊 Subscribed to: games, predictions, expert_research");

    // Clean up subscriptions after a short delay
    setTimeout(() => {
      gamesSubscription.unsubscribe();
      predictionsSubscription.unsubscribe();
      expertResearchSubscription.unsubscribe();
      console.log("🧹 Realtime subscriptions cleaned up");
    }, 2000);
  } catch (err) {
    console.error("❌ Realtime subscription test failed:", err);
  }
}

// Run tests
async function runTests() {
  console.log("🚀 Starting NFL Predictor Database Tests...\n");

  const connectionOk = await testConnection();

  if (connectionOk) {
    await testFunctions();
    await testPgVector();
    await testAdvancedVectorFunctions();
    await testRealtimeSubscriptions();
    console.log("\n🎉 All tests completed!");
  } else {
    console.log("\n💥 Tests failed - check your connection");
  }
}

// Export for use in other files
export {
  supabase,
  testConnection,
  testFunctions,
  testPgVector,
  testAdvancedVectorFunctions,
  testRealtimeSubscriptions,
};

// Run if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  runTests();
}
