import React, { useState, useCallback, useMemo } from 'react';
import {
  Box, Paper, Typography, Avatar, TextField, Button, Link, Tabs, Tab,
  Checkbox, FormControlLabel, InputAdornment, IconButton, Alert, Fade,
  Divider, useTheme, alpha, CircularProgress, Tooltip
} from '@mui/material';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import EmailIcon from '@mui/icons-material/Email';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import BadgeIcon from '@mui/icons-material/Badge';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import LoginIcon from '@mui/icons-material/Login';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import SecurityIcon from '@mui/icons-material/Security';
import axios from 'axios';

const BACKEND_BASE_URL = process.env.REACT_APP_API_BASE_URL;

// Custom styled components moved outside to prevent re-creation
const StyledTextField = React.memo(({ children, ...props }) => {
  const theme = useTheme();
  return (
    <TextField
      {...props}
      variant="outlined"
      size="small"
      sx={{
        '& .MuiOutlinedInput-root': {
          borderRadius: 2,
          transition: 'all 0.2s ease-in-out',
          backgroundColor: 'rgba(255, 255, 255, 0.8)',
          '&:hover': {
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: theme.palette.primary.main,
            },
          },
          '&.Mui-focused': {
            backgroundColor: 'rgba(255, 255, 255, 1)',
            '& .MuiOutlinedInput-notchedOutline': {
              borderWidth: '2px',
            },
          },
        },
        '& .MuiInputLabel-root': {
          fontWeight: 500,
        },
        '& .MuiInputLabel-root.Mui-focused': {
          color: theme.palette.primary.main,
        },
        ...props.sx,
      }}
    >
      {children}
    </TextField>
  );
});

const StyledButton = React.memo(({ children, loading, ...props }) => {
  const theme = useTheme();
  return (
    <Button
      {...props}
      disabled={props.disabled || loading}
      sx={{
        borderRadius: 2,
        py: 1.2,
        fontSize: '0.9rem',
        fontWeight: 600,
        textTransform: 'none',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        boxShadow: '0 4px 15px 0 rgba(102, 126, 234, 0.3)',
        transition: 'all 0.3s ease',
        position: 'relative',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 6px 20px 0 rgba(102, 126, 234, 0.4)',
          background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
        },
        '&:active': {
          transform: 'translateY(0)',
        },
        '&:disabled': {
          background: alpha(theme.palette.primary.main, 0.5),
          transform: 'none',
          boxShadow: 'none',
        },
        ...props.sx,
      }}
    >
      {loading && (
        <CircularProgress
          size={20}
          sx={{
            position: 'absolute',
            color: 'white',
          }}
        />
      )}
      <span style={{ visibility: loading ? 'hidden' : 'visible' }}>
        {children}
      </span>
    </Button>
  );
});

function LoginSignupPage({ onLogin }) {
  const theme = useTheme();
  const [tab, setTab] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Login state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

  // Signup state
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [signupConfirmPassword, setSignupConfirmPassword] = useState('');
  const [signupEmployeeCode, setSignupEmployeeCode] = useState('');
  const [agreeTerms, setAgreeTerms] = useState(false);

  // Error and success
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Validation states
  const [fieldErrors, setFieldErrors] = useState({});

  // Memoized validation functions
  const validateEmail = useCallback((email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }, []);

  const validatePassword = useCallback((password) => {
    return password.length >= 8;
  }, []);

  const validateEmployeeCode = useCallback((code) => {
    return code.length >= 3;
  }, []);

  // Password strength calculator
  const getPasswordStrength = useCallback((password) => {
    let strength = 0;
    if (password.length >= 8) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[a-z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^A-Za-z0-9]/.test(password)) strength += 1;
    return strength;
  }, []);

  // Memoized password strength indicator
  const passwordStrengthColor = useMemo(() => {
    const strength = getPasswordStrength(signupPassword);
    if (strength < 2) return 'error';
    if (strength < 4) return 'warning';
    return 'success';
  }, [signupPassword, getPasswordStrength]);

  const passwordStrengthText = useMemo(() => {
    const strength = getPasswordStrength(signupPassword);
    if (strength < 2) return 'Weak';
    if (strength < 4) return 'Medium';
    return 'Strong';
  }, [signupPassword, getPasswordStrength]);

  // Event handlers
  const handleTabChange = useCallback((_, newValue) => {
    setTab(newValue);
    setError('');
    setSuccess('');
    setFieldErrors({});
  }, []);

  const handleLogin = useCallback(async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setFieldErrors({});
    setIsLoading(true);

    // Validation
    const errors = {};
    if (!loginEmail) {
      errors.email = 'Email is required';
    } else if (!validateEmail(loginEmail)) {
      errors.email = 'Please enter a valid email address';
    }
    if (!loginPassword) {
      errors.password = 'Password is required';
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setIsLoading(false);
      return;
    }

    try {
      const res = await axios.post(`${BACKEND_BASE_URL}/auth/login`, {
        email: loginEmail.trim().toLowerCase(),
        password: loginPassword,
      }, {
        timeout: 10000, // 10 second timeout
      });

      setSuccess('Login successful! Redirecting...');

      // Store token if remember me is checked
      if (rememberMe) {
        localStorage.setItem('rememberMe', 'true');
        localStorage.setItem('userEmail', loginEmail.trim().toLowerCase());
      }

      setTimeout(() => {
        onLogin(res.data.access_token, res.data.user);
      }, 1000);
    } catch (err) {
      console.error('Login error:', err);
      if (err.code === 'ECONNABORTED') {
        setError('Request timeout. Please check your connection and try again.');
      } else {
        setError(err.response?.data?.error || 'Login failed. Please check your credentials and try again.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [loginEmail, loginPassword, rememberMe, validateEmail, onLogin]);

  const handleSignup = useCallback(async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setFieldErrors({});
    setIsLoading(true);

    // Validation
    const errors = {};
    if (!signupEmployeeCode) {
      errors.employeeCode = 'Employee code is required';
    } else if (!validateEmployeeCode(signupEmployeeCode)) {
      errors.employeeCode = 'Employee code must be at least 3 characters';
    }

    if (!signupEmail) {
      errors.email = 'Email is required';
    } else if (!validateEmail(signupEmail)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!signupPassword) {
      errors.password = 'Password is required';
    } else if (!validatePassword(signupPassword)) {
      errors.password = 'Password must be at least 8 characters long';
    }

    if (!signupConfirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (signupPassword !== signupConfirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    if (!agreeTerms) {
      errors.terms = 'You must agree to the Terms of Service and Privacy Policy';
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setIsLoading(false);
      return;
    }

    try {
      const res = await axios.post(`${BACKEND_BASE_URL}/auth/signup`, {
        email: signupEmail.trim().toLowerCase(),
        password: signupPassword,
        employee_code: signupEmployeeCode.trim(),
      }, {
        timeout: 10000, // 10 second timeout
      });

      setSuccess('Account created successfully! Redirecting...');
      setTimeout(() => {
        onLogin(res.data.access_token, res.data.user);
      }, 1000);
    } catch (err) {
      console.error('Signup error:', err);
      if (err.code === 'ECONNABORTED') {
        setError('Request timeout. Please check your connection and try again.');
      } else {
        setError(err.response?.data?.error || 'Signup failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [signupEmail, signupPassword, signupConfirmPassword, signupEmployeeCode, agreeTerms, validateEmail, validatePassword, validateEmployeeCode, onLogin]);

  // Load remembered email on component mount
  React.useEffect(() => {
    const remembered = localStorage.getItem('rememberMe');
    const savedEmail = localStorage.getItem('userEmail');
    if (remembered === 'true' && savedEmail) {
      setLoginEmail(savedEmail);
      setRememberMe(true);
    }
  }, []);

  return (
    <Box sx={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 1,
      position: 'relative',
      '&::before': {
        content: '""',
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.05"%3E%3Cpath d="M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat',
      }
    }}>
      <Paper elevation={24} sx={{
        p: 3,
        width: { xs: '95%', sm: 400 },
        maxWidth: 420,
        borderRadius: 4,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        background: 'rgba(255, 255, 255, 0.95)',
        backdropFilter: 'blur(20px)',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.15)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        position: 'relative',
        zIndex: 1,
      }}>
        <Avatar sx={{
          width: 64,
          height: 64,
          mb: 2,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          boxShadow: '0 8px 32px rgba(102, 126, 234, 0.3)',
          transition: 'transform 0.3s ease',
          '&:hover': {
            transform: 'scale(1.05)',
          }
        }}>
          <LockOutlinedIcon sx={{ fontSize: 32, color: 'white' }} />
        </Avatar>

        <Typography variant="h4" fontWeight={700} align="center" gutterBottom sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          color: 'transparent',
          fontSize: { xs: '1.5rem', sm: '2rem' }
        }}>
          HR Assistant
        </Typography>

        <Typography variant="body2" color="text.secondary" align="center" mb={3} sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          fontSize: '0.9rem'
        }}>
          <SecurityIcon fontSize="small" />
          Employee Self-Service Portal
        </Typography>

        <Tabs
          value={tab}
          onChange={handleTabChange}
          centered
          sx={{
            mb: 3,
            width: '100%',
            '& .MuiTab-root': {
              fontWeight: 600,
              fontSize: '0.9rem',
              textTransform: 'none',
              minWidth: 0,
              flex: 1,
              transition: 'all 0.2s ease',
              minHeight: 48,
              '&:hover': {
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
              }
            },
            '& .MuiTabs-indicator': {
              height: 3,
              borderRadius: 1.5,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }
          }}
        >
          <Tab
            icon={<LoginIcon fontSize="small" />}
            label="Login"
            iconPosition="start"
            sx={{ gap: 0.5 }}
          />
          <Tab
            icon={<PersonAddIcon fontSize="small" />}
            label="Sign Up"
            iconPosition="start"
            sx={{ gap: 0.5 }}
          />
        </Tabs>

        <Divider sx={{ width: '100%', mb: 3 }} />

        {/* Success/Error Messages */}
        <Fade in={!!(error || success)} timeout={500}>
          <Box sx={{ width: '100%', mb: error || success ? 2 : 0 }}>
            {error && (
              <Alert severity="error" sx={{ borderRadius: 2, fontSize: '0.85rem' }}>
                {error}
              </Alert>
            )}
            {success && (
              <Alert severity="success" sx={{ borderRadius: 2, fontSize: '0.85rem' }} icon={<CheckCircleIcon />}>
                {success}
              </Alert>
            )}
          </Box>
        </Fade>

        {tab === 0 ? (
          <Box component="form" onSubmit={handleLogin} noValidate sx={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box sx={{ textAlign: 'center', mb: 1 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom sx={{ fontSize: '1.1rem' }}>
                Welcome Back!
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
                Sign in to access your HR assistant
              </Typography>
            </Box>

            <StyledTextField
              label="Email Address"
              type="email"
              value={loginEmail}
              onChange={(e) => setLoginEmail(e.target.value)}
              required
              fullWidth
              autoComplete="email"
              error={!!fieldErrors.email}
              helperText={fieldErrors.email}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <EmailIcon color="action" fontSize="small" />
                  </InputAdornment>
                )
              }}
              placeholder="Enter your company email"
            />

            <StyledTextField
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={loginPassword}
              onChange={(e) => setLoginPassword(e.target.value)}
              required
              fullWidth
              autoComplete="current-password"
              error={!!fieldErrors.password}
              helperText={fieldErrors.password}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <VpnKeyIcon color="action" fontSize="small" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <Tooltip title={showPassword ? 'Hide password' : 'Show password'}>
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                        size="small"
                      >
                        {showPassword ? <VisibilityOffIcon fontSize="small" /> : <VisibilityIcon fontSize="small" />}
                      </IconButton>
                    </Tooltip>
                  </InputAdornment>
                )
              }}
              placeholder="Enter your password"
            />

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    size="small"
                  />
                }
                label={<Typography variant="body2" sx={{ fontSize: '0.85rem' }}>Remember me</Typography>}
              />
              <Link href="#" underline="hover" variant="body2" sx={{ fontWeight: 500, fontSize: '0.85rem' }}>
                Forgot password?
              </Link>
            </Box>

            <StyledButton
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              loading={isLoading}
              sx={{ mt: 1 }}
            >
              {isLoading ? 'Signing In...' : 'Sign In'}
            </StyledButton>

            <Typography variant="body2" align="center" mt={1} sx={{ fontSize: '0.85rem' }}>
              Don't have an account?{' '}
              <Link
                component="button"
                type="button"
                onClick={() => setTab(1)}
                sx={{ fontWeight: 600, cursor: 'pointer' }}
              >
                Create one now
              </Link>
            </Typography>
          </Box>
        ) : (
          <Box component="form" onSubmit={handleSignup} noValidate sx={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box sx={{ textAlign: 'center', mb: 1 }}>
              <Typography variant="h6" fontWeight={600} gutterBottom sx={{ fontSize: '1.1rem' }}>
                Create Your Account
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
                Join us to access your HR assistant
              </Typography>
            </Box>

            <StyledTextField
              label="Employee Code"
              value={signupEmployeeCode}
              onChange={(e) => setSignupEmployeeCode(e.target.value)}
              required
              fullWidth
              error={!!fieldErrors.employeeCode}
              helperText={fieldErrors.employeeCode}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <BadgeIcon color="action" fontSize="small" />
                  </InputAdornment>
                )
              }}
              placeholder="Enter your employee code"
            />

            <StyledTextField
              label="Email Address"
              type="email"
              value={signupEmail}
              onChange={(e) => setSignupEmail(e.target.value)}
              required
              fullWidth
              autoComplete="email"
              error={!!fieldErrors.email}
              helperText={fieldErrors.email}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <EmailIcon color="action" fontSize="small" />
                  </InputAdornment>
                )
              }}
              placeholder="Enter your company email"
            />

            <StyledTextField
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={signupPassword}
              onChange={(e) => setSignupPassword(e.target.value)}
              required
              fullWidth
              autoComplete="new-password"
              error={!!fieldErrors.password}
              helperText={fieldErrors.password || (signupPassword && `Password strength: ${passwordStrengthText}`)}
              FormHelperTextProps={{
                sx: { color: signupPassword ? `${passwordStrengthColor}.main` : 'text.secondary' }
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <VpnKeyIcon color="action" fontSize="small" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <Tooltip title={showPassword ? 'Hide password' : 'Show password'}>
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                        size="small"
                      >
                        {showPassword ? <VisibilityOffIcon fontSize="small" /> : <VisibilityIcon fontSize="small" />}
                      </IconButton>
                    </Tooltip>
                  </InputAdornment>
                )
              }}
              placeholder="Create a strong password (min 8 characters)"
            />

            <StyledTextField
              label="Confirm Password"
              type={showConfirmPassword ? 'text' : 'password'}
              value={signupConfirmPassword}
              onChange={(e) => setSignupConfirmPassword(e.target.value)}
              required
              fullWidth
              autoComplete="new-password"
              error={!!fieldErrors.confirmPassword}
              helperText={fieldErrors.confirmPassword}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <VpnKeyIcon color="action" fontSize="small" />
                  </InputAdornment>
                ),
                endAdornment: (
                  <InputAdornment position="end">
                    <Tooltip title={showConfirmPassword ? 'Hide password' : 'Show password'}>
                      <IconButton
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        edge="end"
                        size="small"
                      >
                        {showConfirmPassword ? <VisibilityOffIcon fontSize="small" /> : <VisibilityIcon fontSize="small" />}
                      </IconButton>
                    </Tooltip>
                  </InputAdornment>
                )
              }}
              placeholder="Confirm your password"
            />

            <FormControlLabel
              control={
                <Checkbox
                  checked={agreeTerms}
                  onChange={(e) => setAgreeTerms(e.target.checked)}
                  size="small"
                />
              }
              label={
                <Typography variant="body2" sx={{ fontSize: '0.85rem' }}>
                  I agree to the{' '}
                  <Link href="#" underline="hover" sx={{ fontWeight: 500 }}>
                    Terms of Service
                  </Link>
                  {' '}and{' '}
                  <Link href="#" underline="hover" sx={{ fontWeight: 500 }}>
                    Privacy Policy
                  </Link>
                </Typography>
              }
            />

            {fieldErrors.terms && (
              <Typography color="error" variant="body2" sx={{ fontSize: '0.75rem', mt: -1 }}>
                {fieldErrors.terms}
              </Typography>
            )}

            <StyledButton
              type="submit"
              variant="contained"
              size="large"
              fullWidth
              loading={isLoading}
              sx={{ mt: 1 }}
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </StyledButton>

            <Typography variant="body2" align="center" mt={1} sx={{ fontSize: '0.85rem' }}>
              Already have an account?{' '}
              <Link
                component="button"
                type="button"
                onClick={() => setTab(0)}
                sx={{ fontWeight: 600, cursor: 'pointer' }}
              >
                Sign In
              </Link>
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
}

export default LoginSignupPage;