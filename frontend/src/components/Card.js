import React from 'react';
import './Card.css';

function Card({ title, value, icon, type, subtext }) {
  return (
    <div className={`card ${type || ''}`}>
      <div className="card-header">
        <h3>{title}</h3>
        {icon && <span className="card-icon">{icon}</span>}
      </div>
      <div className="card-value">
        {value}
      </div>
      {subtext && <div className="card-subtext">{subtext}</div>}
    </div>
  );
}

export default Card;