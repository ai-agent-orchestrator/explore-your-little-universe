import test from 'node:test';
import assert from 'node:assert/strict';
import {createSSEParser,watchReading,loadSession,saveSession} from './api.js';

test('SSE frames survive chunk boundaries, split CRLF and multiline data',()=>{
 const events=[];const parser=createSSEParser(e=>events.push(e));
 for(const piece of ['id: 4\r','\nevent: report.completed\r\nda','ta: {"text":\r\ndata: "한글"}\r\n\r','\n'])parser.push(piece);
 assert.deepEqual(events,[{id:4,event:'report.completed',data:'{"text":\n"한글"}'}]);
 assert.equal(parser.end(),4);
});

test('SSE cursor suppresses replayed IDs and ignores heartbeats and partial frames',()=>{
 const events=[];const parser=createSSEParser(e=>events.push(e),5);
 parser.push(': heartbeat\n\nid: 4\ndata: {}\n\nid: 6\ndata: {}\n\nid: 6\ndata: {}\n\nid: 7\ndata: unfinished');
 assert.equal(events.length,1);assert.equal(events[0].id,6);assert.equal(parser.end(),6);
});

test('fetch SSE sends bearer and cursor as headers and decodes split UTF-8',async()=>{
 const previous=globalThis.fetch;let request;
 const text=new TextEncoder().encode('id: 8\nevent: graph.completed\ndata: {"text":"마음"}\n\n');
 globalThis.fetch=async(url,options)=>{
  request={url,options};return new Response(new ReadableStream({start(c){for(const byte of text)c.enqueue(new Uint8Array([byte]));c.close()}}),{headers:{'Content-Type':'text/event-stream'}});
 };
 try{
  const events=[];const cursor=await watchReading('http://127.0.0.1:8017',{session_id:'some-id',session_token:'secret-token'},e=>events.push(e),{after:7});
  assert.equal(cursor,8);assert.equal(events[0].data.text,'마음');
  assert.equal(request.options.headers.Authorization,'Bearer secret-token');
  assert.equal(request.options.headers['Last-Event-ID'],'7');
  assert.ok(!request.url.includes('secret-token'));assert.ok(!request.url.includes('?'));
 }finally{globalThis.fetch=previous}
});

test('session storage failures are recoverable without leaking tokens',()=>{
 const previous=globalThis.sessionStorage;
 globalThis.sessionStorage={getItem(){throw Error('blocked')},setItem(){throw Error('blocked')},removeItem(){throw Error('blocked')}};
 try{assert.equal(loadSession(),null);assert.equal(saveSession({session_token:'private'}),false)}finally{globalThis.sessionStorage=previous}
});
