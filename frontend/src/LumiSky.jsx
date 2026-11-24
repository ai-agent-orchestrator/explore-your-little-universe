import React from 'react';
import {Lumi} from './Lumi.jsx';

export function LumiSky(){
 return <div className="lumi-sky" aria-hidden="true">{[0,1,2,3,4].map(index=><span className={`sky-lumi sky-lumi-${index}`} key={index}><Lumi code="ENFP" colorOverride="#ffe49a"/></span>)}</div>;
}
