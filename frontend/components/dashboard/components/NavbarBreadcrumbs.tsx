import * as React from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { styled } from '@mui/material/styles';
import Typography from '@mui/material/Typography';
import MuiLink from '@mui/material/Link';
import Breadcrumbs, { breadcrumbsClasses } from '@mui/material/Breadcrumbs';
import NavigateNextRoundedIcon from '@mui/icons-material/NavigateNextRounded';

const StyledBreadcrumbs = styled(Breadcrumbs)(({ theme }) => ({
  margin: theme.spacing(1, 0),
  [`& .${breadcrumbsClasses.separator}`]: {
    color: (theme.vars || theme).palette.action.disabled,
    margin: 1,
  },
  [`& .${breadcrumbsClasses.ol}`]: {
    alignItems: 'center',
  },
}));

export default function NavbarBreadcrumbs() {
  const router = useRouter();
  
  // Define route mappings for breadcrumbs
  const routeMap: { [key: string]: string } = {
    '/': 'Login',
    '/dashboard': 'Dashboard',
    '/ai-dashboard': 'AI Analytics',
    '/template-dashboard': 'Template Dashboard',
    '/login': 'Login',
  };

  // Generate breadcrumb items based on current route
  const generateBreadcrumbs = () => {
    const pathSegments = router.asPath.split('/').filter(segment => segment);
    const breadcrumbItems = [];

    // Always start with Home (Dashboard)
    breadcrumbItems.push({
      label: 'Home',
      href: '/dashboard',
      isActive: router.pathname === '/dashboard'
    });

    // Add current page if it's not the dashboard
    if (router.pathname !== '/dashboard') {
      const currentPageName = routeMap[router.pathname] || 'Current Page';
      breadcrumbItems.push({
        label: currentPageName,
        href: router.pathname,
        isActive: true
      });
    }

    return breadcrumbItems;
  };

  const breadcrumbItems = generateBreadcrumbs();

  return (
    <StyledBreadcrumbs
      aria-label="breadcrumb"
      separator={<NavigateNextRoundedIcon fontSize="small" />}
    >
      {breadcrumbItems.map((item, index) => {
        const isLast = index === breadcrumbItems.length - 1;
        
        if (isLast || item.isActive) {
          return (
            <Typography 
              key={item.href}
              variant="body1" 
              sx={{ color: 'text.primary', fontWeight: 600 }}
            >
              {item.label}
            </Typography>
          );
        }
        
        return (
          <Link key={item.href} href={item.href} passHref legacyBehavior>
            <MuiLink 
              variant="body1" 
              sx={{ 
                color: 'text.secondary',
                textDecoration: 'none',
                '&:hover': {
                  textDecoration: 'underline',
                  color: 'primary.main'
                }
              }}
            >
              {item.label}
            </MuiLink>
          </Link>
        );
      })}
    </StyledBreadcrumbs>
  );
}
