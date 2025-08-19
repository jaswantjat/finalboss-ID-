# Docker PORT Environment Variable Handling Guide

## 🔍 **Problem Analysis**

### **Root Cause**
The error `'$PORT' is not a valid integer` occurs when:
1. **Railway's startCommand** overrides Dockerfile CMD
2. **No shell expansion** happens in Railway's command execution
3. **uvicorn receives literal `"$PORT"`** instead of integer value

### **Technical Details**

#### **Docker CMD Forms**
```dockerfile
# ❌ EXEC FORM (no variable expansion)
CMD ["uvicorn", "app:main", "--port", "$PORT"]
# Result: uvicorn gets literal "$PORT" string

# ✅ SHELL FORM (with variable expansion)  
CMD uvicorn app:main --port ${PORT:-8000}
# Result: Shell expands ${PORT:-8000} to actual number

# ✅ EXEC + SHELL (hybrid - best practice)
CMD ["sh", "-c", "uvicorn app:main --port ${PORT:-8000}"]
# Result: Shell expansion in exec form
```

#### **Railway Behavior**
- `startCommand` in railway.toml **overrides** Dockerfile CMD
- Railway executes startCommand **without shell** by default
- Environment variables remain as literal strings

## 🛠️ **Solutions**

### **Solution 1: Remove startCommand Override (Recommended)**

**File: `railway.toml`**
```toml
[deploy]
# Let Dockerfile handle startup with proper shell expansion
# startCommand = "uvicorn api_service:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
```

**File: `Dockerfile`**
```dockerfile
CMD ["sh", "-c", "uvicorn api_service:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### **Solution 2: Python Launcher (Most Robust)**

**File: `run_server.py`**
```python
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))  # Guaranteed integer
    uvicorn.run("api_service:app", host="0.0.0.0", port=port)
```

**File: `Dockerfile`**
```dockerfile
CMD ["python", "run_server.py"]
```

### **Solution 3: Shell Wrapper in startCommand**

**File: `railway.toml`**
```toml
[deploy]
startCommand = "sh -c 'uvicorn api_service:app --host 0.0.0.0 --port ${PORT:-8000}'"
```

## 🧪 **Testing**

### **Local Testing**
```bash
# Test Python launcher
python test_port_handling.py

# Test Docker build
python test_port_handling.py --docker

# Manual Docker test
docker build -t test-app .
docker run -e PORT=3000 -p 3000:3000 test-app
```

### **Railway Testing**
1. Deploy with each solution
2. Check logs for: `Uvicorn running on http://0.0.0.0:XXXX`
3. Verify health check: `curl https://your-app.railway.app/health`

## 📊 **Solution Comparison**

| Solution | Pros | Cons | Best For |
|----------|------|------|----------|
| Remove startCommand | Simple, uses Docker best practices | Requires Dockerfile changes | Most deployments |
| Python Launcher | Platform agnostic, robust error handling | Extra file | Production apps |
| Shell Wrapper | Keeps railway.toml control | Platform dependent | Railway-specific |

## 🔧 **Implementation Steps**

### **Quick Fix (5 minutes)**
1. Comment out `startCommand` in `railway.toml`
2. Ensure Dockerfile uses: `CMD ["sh", "-c", "uvicorn ... --port ${PORT:-8000}"]`
3. Redeploy

### **Robust Fix (10 minutes)**
1. Use `run_server.py` launcher
2. Update Dockerfile: `CMD ["python", "run_server.py"]`
3. Remove `startCommand` from `railway.toml`
4. Test locally and deploy

## 🚀 **Platform Compatibility**

This solution works on:
- ✅ Railway.app
- ✅ Heroku
- ✅ Google Cloud Run
- ✅ AWS ECS/Fargate
- ✅ Azure Container Instances
- ✅ Local Docker

## 🔍 **Debugging**

### **Check Environment Variables**
```bash
# In container
echo $PORT
env | grep PORT

# In Railway logs
railway logs
```

### **Verify uvicorn Command**
```bash
# Should see integer, not $PORT
ps aux | grep uvicorn
```

### **Test Health Check**
```bash
curl -v http://localhost:$PORT/health
```
