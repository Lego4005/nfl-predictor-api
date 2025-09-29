import React from 'react'

interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
    href: string
    children: React.ReactNode
}

const Link: React.FC<LinkProps> = ({ href, children, className, ...props }) => {
    return (
        <a
            href={href}
            className={className}
            {...props}
        >
            {children}
        </a>
    )
}

export default Link