export function evidenceCypher(path){
 const seed=path.via[0];
 const cardId=/^(?:scenario-\d+|daily-\d{2}-\d{2}|mbti-[a-z]{4}-\d{2}|zodiac-[a-z]+-\d{2})$/;
 if(!cardId.test(seed)||!cardId.test(path.chunk.id)||!/^[IESNTFJP]$/.test(path.trait)||!/^[a-z]+$/.test(path.tip.id))throw Error('Invalid graph identifier');
 return `// Neo4j Browser: :use mbti-zodiac\nMATCH p = (seed:RagChunk {id:'${seed}'})<-[:FROM_CHUNK]-(t:SharedTrait {key:'${path.trait}'})\n          -[:FROM_CHUNK]->(other:RagChunk {id:'${path.chunk.id}'})\n          <-[:FROM_CHUNK]-(tip:RagTip {id:'${path.tip.id}'})\nMATCH (t)-[:SUGGESTS]->(tip)\nMATCH q = (other)-[:FROM_DOCUMENT]->(:RagDocument)\nRETURN p, q;`;
}
