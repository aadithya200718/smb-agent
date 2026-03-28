import { forwardRef } from 'react';

const Input = forwardRef(({
  label,
  error,
  id,
  className = '',
  type = 'text',
  helperText,
  ...props
}, ref) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
  const errorId = error ? `${inputId}-error` : undefined;

  return (
    <div className={className}>
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-gray-300 mb-1.5">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          ref={ref}
          id={inputId}
          type={type}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={errorId}
          className={`
            block w-full rounded-lg bg-white/[0.04] border px-3.5 py-2.5 text-gray-100 text-sm
            placeholder:text-gray-500
            transition-all duration-200
            ${error
              ? 'border-red-500/50 text-red-300 placeholder:text-red-400/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/30'
              : 'border-white/[0.08] hover:border-white/[0.15] focus:border-primary-500/50 focus:ring-1 focus:ring-primary-500/30'
            }
            ${props.disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
          {...props}
        />
      </div>
      {error && (
        <p className="mt-1.5 flex items-center text-sm text-red-400" id={errorId}>
          {error}
        </p>
      )}
      {helperText && !error && (
        <p className="mt-1.5 text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';
export default Input;
