const meanings = {
 fool:['작은 시작을 허용해 보세요.','시작 전에 필요한 준비 하나를 확인해 보세요.'],
 magician:['이미 가진 도구와 강점을 활용해 보세요.','흩어진 관심을 한 가지 행동에 모아 보세요.'],
 'high-priestess':['잠시 멈추고 마음속 반응을 들어보세요.','느낌과 확인된 사실을 나눠 적어보세요.'],
 empress:['자신과 주변을 돌보는 시간을 만들어 보세요.','돌봄에 지친 자신에게도 여유를 주세요.'],
 emperor:['지금 필요한 기준과 경계를 정해 보세요.','너무 엄격한 기준을 조금 느슨하게 해보세요.'],
 hierophant:['도움이 된 배움과 조언을 돌아보세요.','익숙한 규칙이 지금도 맞는지 살펴보세요.'],
 lovers:['중요하게 여기는 가치에 맞춰 선택해 보세요.','서로 다른 기대를 대화로 확인해 보세요.'],
 chariot:['목표를 정하고 한 걸음 움직여 보세요.','속도를 줄이고 방향을 다시 확인해 보세요.'],
 strength:['강요보다 인내와 다정함을 선택해 보세요.','자신에게 지나치게 버티라고 요구하지 마세요.'],
 hermit:['혼자 생각을 정리할 시간을 가져보세요.','혼자 해결하기 어렵다면 도움을 청해 보세요.'],
 'wheel-of-fortune':['변화 속에서 조절할 수 있는 것에 집중해 보세요.','반복되는 패턴을 한 가지 찾아보세요.'],
 justice:['사실과 책임을 균형 있게 살펴보세요.','자신이나 타인에 대한 단정을 잠시 미뤄보세요.'],
 'hanged-man':['다른 각도에서 상황을 바라보세요.','기다리는 이유와 필요한 행동을 구분해 보세요.'],
 death:['마무리할 것과 새로 시작할 것을 적어보세요.','변화를 어렵게 하는 익숙함을 살펴보세요.'],
 temperance:['서로 다른 필요 사이에서 균형을 찾아보세요.','일상의 속도와 휴식을 다시 조절해 보세요.'],
 devil:['반복되는 습관과 그 대가를 살펴보세요.','자신의 선택권을 되찾을 작은 방법을 찾아보세요.'],
 tower:['흔들린 기대를 살피고 작은 기반부터 세워보세요.','피하고 있던 변화를 안전한 속도로 살펴보세요.'],
 star:['회복에 도움이 되는 작은 희망을 적어보세요.','큰 확신 대신 오늘 가능한 돌봄을 선택해 보세요.'],
 moon:['불확실한 상황에서는 확인할 시간을 주세요.','불안과 사실을 구분할 단서를 찾아보세요.'],
 sun:['작은 성취를 알아보고 나눠보세요.','완벽한 기쁨을 기다리지 말고 작은 즐거움을 찾아보세요.'],
 judgement:['지난 경험에서 배운 점을 정리해 보세요.','자책보다 다음에 바꿀 행동 하나를 골라보세요.'],
 world:['마친 과정을 인정하고 다음 장을 준비해 보세요.','남아 있는 작은 마무리 하나를 정해 보세요.']
};
const button=document.querySelector('#draw');
const status=document.querySelector('#status');
const cards=document.querySelector('#cards');
function randomInt(max){
 const sample=new Uint32Array(1),limit=2**32-(2**32%max);
 do{crypto.getRandomValues(sample);}while(sample[0]>=limit);
 return sample[0]%max;
}
function render(deck){
 const pool=[...deck],positions=['과거 · 돌아보기','현재 · 살펴보기','미래 · 생각해 볼 방향'];
 cards.replaceChildren();
 for(let i=0;i<3;i++){
  const card=pool.splice(randomInt(pool.length),1)[0],reversed=randomInt(2)===1;
  const article=document.createElement('article');
  const position=document.createElement('p');position.className='position';position.textContent=positions[i];
  const frame=document.createElement('div');frame.className='frame';
  const image=document.createElement('img');image.src=`./assets/${card.slug}.png`;image.alt=`${card.name_ko} · ${reversed?'역방향':'정방향'}`;
  if(reversed)image.className='reversed';frame.append(image);
  const title=document.createElement('h2');title.textContent=card.name_ko;
  const orientation=document.createElement('span');orientation.className='orientation';orientation.textContent=`${card.name_en} · ${reversed?'역방향':'정방향'}`;
  const meaning=document.createElement('p');meaning.className='meaning';meaning.textContent=meanings[card.slug][Number(reversed)];
  article.append(position,frame,title,orientation,meaning);cards.append(article);
 }
 status.textContent='서로 다른 카드 3장을 뽑았어요.';button.textContent='다시 뽑기';
}
try{
 const response=await fetch('./assets/major-arcana.json');if(!response.ok)throw new Error('deck');
 const {cards:deck}=await response.json();
 if(deck.length!==22||deck.some(card=>!meanings[card.slug]))throw new Error('deck');
 button.disabled=false;button.textContent='카드 3장 뽑기';status.textContent='준비되면 카드를 뽑아보세요.';
 button.addEventListener('click',()=>render(deck));
}catch{status.textContent='카드를 불러오지 못했어요. 잠시 후 새로고침해 주세요.';button.textContent='불러오기 실패';}
