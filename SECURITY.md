# Security Guidelines for VoiceNote AI

## 🔒 Environment Variables & Secrets Management

### **Critical Security Rules:**

1. **NEVER commit secrets to Git**
   - API keys, JWT tokens, database passwords, service role keys
   - Always use environment variables for sensitive data

2. **Environment Variable Naming Convention:**
   ```bash
   # ✅ GOOD - Clear naming
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   OPENAI_API_KEY=your_openai_key
   
   # ❌ BAD - Hardcoded in source files
   const apiKey = "sk-1234567890abcdef"
   ```

3. **Required Environment Variables:**
   - `SUPABASE_URL` - Your Supabase project URL
   - `SUPABASE_ANON_KEY` - Public anon key (safe for frontend)
   - `SUPABASE_SERVICE_ROLE_KEY` - **BACKEND ONLY** - Full admin access
   - `OPENAI_API_KEY` - OpenAI API key for transcription/summarization

### **Development Setup:**

1. **Local Development:**
   ```bash
   # Copy example environment file
   cp backend/env.example backend/.env
   
   # Fill in your actual values (NEVER commit this file)
   # backend/.env should be in .gitignore
   ```

2. **Production Deployment (Railway):**
   - Set environment variables in Railway dashboard
   - Never include secrets in railway.json or nixpacks.toml

### **Security Tools Enabled:**

1. **Pre-commit Hooks:**
   ```bash
   # Install pre-commit (run once)
   pip install pre-commit
   pre-commit install
   
   # Now every commit will be scanned for secrets
   ```

2. **Secret Detection:**
   - `detect-secrets` - Scans for various secret patterns
   - `ggshield` - GitGuardian integration
   - `check-private-key` - Detects SSH/TLS private keys

### **If You Accidentally Commit a Secret:**

1. **Immediate Actions:**
   - Revoke the exposed key immediately in the service (Supabase/OpenAI)
   - Generate a new key
   - Update environment variables with new key

2. **Git History Cleanup (Advanced):**
   - Use BFG Repo-Cleaner or git-filter-repo
   - Force push to rewrite history
   - Inform all collaborators to re-clone

### **Code Review Checklist:**

- [ ] No hardcoded API keys, tokens, or passwords
- [ ] All secrets loaded from environment variables
- [ ] No .env files in the commit
- [ ] No debug prints of sensitive data
- [ ] Environment variables properly documented

### **Supabase Security Best Practices:**

1. **Key Usage:**
   - `SUPABASE_ANON_KEY` - Frontend only, limited permissions
   - `SUPABASE_SERVICE_ROLE_KEY` - Backend only, full admin access

2. **Row Level Security (RLS):**
   - Enable RLS on all tables
   - Create policies for user access control
   - Test policies thoroughly

3. **Database Access:**
   - Use service role key only in backend services
   - Never expose service role key to frontend
   - Implement proper authentication flows

## 🚨 Security Incident Response

If GitGuardian or similar tools detect exposed secrets:

1. **Immediate Response:**
   - Revoke compromised credentials
   - Generate new credentials
   - Update all deployment environments

2. **Investigation:**
   - Identify how the secret was exposed
   - Review recent commits and changes
   - Check if unauthorized access occurred

3. **Prevention:**
   - Implement additional security measures
   - Update team training on security practices
   - Review and improve development workflows

## 📞 Security Contact

For security issues or questions:
- Create a private issue in this repository
- Follow responsible disclosure practices
- Do not publicly disclose security vulnerabilities

---

**Remember: Security is everyone's responsibility. When in doubt, ask for a security review.**
