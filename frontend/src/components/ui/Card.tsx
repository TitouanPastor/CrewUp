import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

const Card: React.FC<CardProps> = ({ children, className = '', onClick }) => {
  const baseStyles = 'bg-white rounded-xl shadow-sm border border-gray-100 p-4 transition-all duration-200';
  const interactiveStyles = onClick ? 'cursor-pointer hover:shadow-md active:scale-[0.99]' : '';

  return (
    <div 
      className={`${baseStyles} ${interactiveStyles} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

export default Card;
